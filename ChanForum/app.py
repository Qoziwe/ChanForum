from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os
import hashlib
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'yourmom')  # your mom

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
db_pathpost = os.path.join(BASE_DIR, 'db', 'databasepost.db')
db_pathusers = os.path.join(BASE_DIR, 'db', 'databaseusers.db')
Error = None

@app.route("/")
def mainpage():
    try:
        # Инициализация переменных
        username = None
        profile_image = None
        user_id = None
        user_liked_posts = []
        friends = []

        if 'user_id' in session:
            user_id = session['user_id']
            with sqlite3.connect(db_pathusers) as conn_users:
                conn_users.row_factory = sqlite3.Row
                user = conn_users.execute(
                    "SELECT username, profile_image, uniq_id FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()

                if user:
                    username = user['username']
                    profile_image = user['profile_image']
                    logged_in_uniq_id = user['uniq_id']
                    
                    # Получаем друзей через связующую таблицу
                    friends_data = conn_users.execute(
                        """SELECT u.uniq_id, u.username, u.profile_image 
                           FROM users u 
                           JOIN user_friends uf ON u.uniq_id = uf.friend_id 
                           WHERE uf.user_id = ?""",
                        (logged_in_uniq_id,)
                    ).fetchall()
                    
                    if friends_data:
                        # Сохраняем данные о друзьях в список
                        friends = [
                            {
                                'uniq_id': friend['uniq_id'],
                                'username': friend['username'],
                                'profile_image': friend['profile_image']
                            }
                            for friend in friends_data
                        ]

        # Загружаем посты
        with sqlite3.connect(db_pathpost) as conn_posts:
            conn_posts.row_factory = sqlite3.Row
            posts = conn_posts.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()

            # Загружаем лайки текущего пользователя
            if user_id:
                liked_posts = conn_posts.execute(
                    "SELECT post_id FROM post_likes WHERE user_id = ?",
                    (user_id,)
                ).fetchall()
                user_liked_posts = [row['post_id'] for row in liked_posts]

        # Преобразуем посты в список словарей
        post_list = [dict(post) for post in posts]

        # Получаем уникальные идентификаторы пользователей из постов
        user_ids = {post['user_uniq_id'] for post in post_list}

    # Добавляем авторов к постам
        if user_ids:
            with sqlite3.connect(db_pathusers) as conn_users:
                conn_users.row_factory = sqlite3.Row
                users = conn_users.execute(
                    f"SELECT uniq_id, username FROM users WHERE uniq_id IN ({','.join(['?'] * len(user_ids))})",
                    tuple(user_ids)
                ).fetchall()

            # Создаем словарь для сопоставления uniq_id с именами пользователей
            user_dict = {user['uniq_id']: user['username'] for user in users}

            for post in post_list:
                post['author'] = user_dict.get(post['user_uniq_id'], 'Unknown')

        return render_template(
            "mainpage.html",
            username=username,
            profile_image=profile_image,
            posts=post_list,
            user_liked_posts=user_liked_posts,
            friends=friends
        )

    except sqlite3.Error as e:
        abort(500, description=f"Database error: {e}")
      
@app.route('/friends', methods=['GET', 'POST'])
def friends():
    username = None
    profile_image = None
    users_list = []

    if 'user_id' in session:
        user_id = session['user_id']
        conn = sqlite3.connect(db_pathusers)
        cursor = conn.cursor()
        user = cursor.execute('SELECT username, profile_image FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        if user:
            username = user[0]
            profile_image = user[1]

        with sqlite3.connect(db_pathusers) as conn_users:
            conn_users.row_factory = sqlite3.Row
            users = conn_users.execute(
                "SELECT username, profile_image, uniq_id FROM users WHERE id != ?",
                (user_id,)
            ).fetchall()

        users_list = [{'username': user['username'], 'profile_image': user['profile_image'], 'uniq_id': user['uniq_id']} for user in users]

    else:
        with sqlite3.connect(db_pathusers) as conn_users:
            conn_users.row_factory = sqlite3.Row
            users = conn_users.execute(
                "SELECT username, profile_image, uniq_id FROM users"
            ).fetchall()

        users_list = [{'username': user['username'], 'profile_image': user['profile_image'], 'uniq_id': user['uniq_id']} for user in users]

    return render_template('friends.html', username=username, profile_image=profile_image, users_list=users_list)

@app.route('/unknownprofile/<string:uniq_id>')
def unknownprofile(uniq_id):
    if 'user_id' not in session:
        flash('Please sign in first.')
        return redirect(url_for('login'))

    username = None
    profile_image = None
    unknowninfo = None
    is_friend = False  # По умолчанию пользователь не является другом

    user_id = session['user_id']

    # Получаем информацию о текущем пользователе
    with sqlite3.connect(db_pathusers) as conn_users:
        cursor = conn_users.cursor()
        cursor.execute('SELECT username, profile_image, uniq_id FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if user:
            username, profile_image, current_uniq_id = user

            # Проверяем, является ли просматриваемый пользователь другом
            cursor.execute('SELECT 1 FROM user_friends WHERE user_id = ? AND friend_id = ?', (current_uniq_id, uniq_id))
            is_friend = cursor.fetchone() is not None

    # Получаем информацию о неизвестном пользователе
    with sqlite3.connect(db_pathusers) as conn_users:
        conn_users.row_factory = sqlite3.Row
        unknown_user = conn_users.execute(
            "SELECT username, profile_image FROM users WHERE uniq_id = ?",
            (uniq_id,)
        ).fetchone()

    if unknown_user:
        unknowninfo = {'username': unknown_user[0], 'profile_image': unknown_user[1]}

    return render_template(
        'unknownprofile.html',
        username=username,
        profile_image=profile_image,
        unknowninfo=unknowninfo,
        is_friend=is_friend
    )

@app.route('/userpost')
def editposts():
    posts = []
    profile_image = None
    username = None
    uniq_id = None

    if 'user_id' in session:
        conn = sqlite3.connect(db_pathusers)
        cursor = conn.cursor()
        cursor.execute("SELECT username, profile_image, uniq_id FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()

        if user:
            username = user[0]
            profile_image = user[1]  # Получаем аватар пользователя
            uniq_id = user[2]       # Получаем uniq_id пользователя

    if uniq_id:
        conn = sqlite3.connect(db_pathpost)
        conn.row_factory = sqlite3.Row
        posts = conn.execute(
            'SELECT * FROM posts WHERE user_uniq_id = ? ORDER BY id DESC', 
            (uniq_id,)
        ).fetchall()  # Выбираем только посты текущего пользователя
        conn.close()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('userpost.html', posts=posts, username=username, profile_image=profile_image, uniq_id=uniq_id)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('User not logged in. Please login.')
        return redirect(url_for('login'))

    username = None
    profile_image = None
    liked_posts = []

    try:
        # Fetch user details
        with sqlite3.connect(db_pathusers) as db:
            cursor = db.cursor()
            cursor.execute("SELECT username, profile_image FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                username = user[0]
                profile_image = user[1] if user[1] else None

        # Fetch liked post IDs
        with sqlite3.connect(db_pathpost) as db:
            cursor = db.cursor()
            cursor.execute("SELECT post_id FROM post_likes WHERE user_id = ?", (session['user_id'],))
            liked_post_ids = cursor.fetchall()
            liked_post_ids = [row[0] for row in liked_post_ids]

            # Fetch liked posts
            if liked_post_ids:
                placeholders = ', '.join(['?'] * len(liked_post_ids))
                query = f"SELECT id, title, description, post_image FROM posts WHERE id IN ({placeholders}) ORDER BY id DESC"
                cursor.execute(query, liked_post_ids)
                liked_posts_data = cursor.fetchall()

                # Convert to list of dictionaries
                liked_posts = [
                    {"id": row[0], "title": row[1], "description": row[2], "post_image": row[3]}
                    for row in liked_posts_data
                ]

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        flash('Error with the database.')
        return redirect(url_for('login'))

    return render_template("profile.html", username=username, profile_image=profile_image, liked_posts=liked_posts)

@app.route('/profile/<string:uniq_id>')
def unknown_profile(uniq_id):
    conn = sqlite3.connect(db_pathusers)
    cursor = conn.cursor()

    cursor.execute('SELECT username, profile_image FROM users WHERE uniq_id = ?', (uniq_id,))
    user_info = cursor.fetchone()

    is_friend = False
    if user_info:
        username, profile_image = user_info
        
        if 'user_id' in session:
            cursor.execute('SELECT uniq_id FROM users WHERE id = ?', (session['user_id'],))
            current_user = cursor.fetchone()
            if current_user:
                current_uniq_id = current_user[0]
                cursor.execute('SELECT 1 FROM user_friends WHERE user_id = ? AND friend_id = ?', (current_uniq_id, uniq_id))
                is_friend = cursor.fetchone() is not None

        conn.close()

        return render_template('profile.html', unknowninfo={
            'username': username,
            'profile_image': profile_image,
            'uniq_id': uniq_id
        }, is_friend=is_friend)

    conn.close()

    return "User not found", 404

@app.route('/unknownuser/<int:post_id>', methods=['GET', 'POST'])
def unknownuser(post_id):
    try:
        # Получаем user_uniq_id автора поста
        with sqlite3.connect(db_pathpost) as conn_posts:
            cursor_posts = conn_posts.cursor()
            cursor_posts.execute("SELECT user_uniq_id FROM posts WHERE id = ?", (post_id,))
            post_author_id = cursor_posts.fetchone()
        
        if not post_author_id:
            abort(404)  # Пост не найден

        post_author_id = post_author_id[0]  # Извлекаем user_uniq_id

        # Проверяем текущего пользователя (если он вошел в систему)
        current_username = None
        current_profile_image = None
        current_user_id = session.get('user_id')  # Получаем ID текущего пользователя из сессии
        uniq_id = None
        is_friend = False  # По умолчанию автор поста не является другом

        if current_user_id:
            with sqlite3.connect(db_pathusers) as conn_users:
                cursor_users = conn_users.cursor()
                cursor_users.execute(
                    "SELECT username, profile_image, uniq_id FROM users WHERE id = ?", 
                    (current_user_id,)
                )
                logged_in_user = cursor_users.fetchone()

                if logged_in_user:
                    current_username, current_profile_image, logged_in_uniq_id = logged_in_user
                    uniq_id = logged_in_uniq_id

                    # Если текущий пользователь — автор поста, перенаправляем в профиль
                    if post_author_id == logged_in_uniq_id:
                        return redirect(url_for('profile'))

                    # Проверяем, является ли автор поста другом текущего пользователя
                    cursor_users.execute('SELECT 1 FROM user_friends WHERE user_id = ? AND friend_id = ?', (logged_in_uniq_id, post_author_id))
                    is_friend = cursor_users.fetchone() is not None

                    # Если метод POST, пытаемся добавить автора поста в друзья
                    if request.method == 'POST' and not is_friend:
                        try:
                            # Обновляем поле friend_id для текущего пользователя
                            cursor_users.execute(
                                "INSERT INTO user_friends (user_id, friend_id) VALUES (?, ?)",
                                (logged_in_uniq_id, post_author_id)
                            )
                            conn_users.commit()
                            flash('User has been added to your friends.')
                            is_friend = True  # Теперь пользователь друг
                        except sqlite3.Error as e:
                            flash(f"Database error: {e}")

        # Получаем информацию об авторе поста
        with sqlite3.connect(db_pathusers) as conn_users:
            cursor_users = conn_users.cursor()
            cursor_users.execute(
                "SELECT username, profile_image FROM users WHERE uniq_id = ?", 
                (post_author_id,)
            )
            author_data = cursor_users.fetchone()
        
        if not author_data:
            abort(404)  # Автор поста не найден

        author_username, author_image = author_data

        return render_template(
            'unknownuser.html',
            author_username=author_username,
            author_image=author_image,
            username=current_username,
            profile_image=current_profile_image,
            is_friend=is_friend
        )

    except sqlite3.Error as e:
        abort(500, description=f"Database error: {e}")

@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user_id' not in session:
        flash('User not logged in. Please login.')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(db_pathusers)
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, profile_image FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()

    
    author = None
    if not user:
        flash('User not found.')
        return redirect(url_for('profile'))

    username, email, profile_image = user

    if request.method == 'POST':
        new_username = request.form.get('username', username)
        new_email = request.form.get('email', email)
        new_password = request.form.get('password')
        profile_image = request.files.get('profile_image')

        author = new_username
        update_query = "UPDATE users SET username = ?, email = ?"
        params = [new_username, new_email]

        if new_password:
            update_query += ", password = ?"
            params.append(generate_password_hash(new_password))

        if profile_image and profile_image.filename:
            filename = secure_filename(profile_image.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', unique_filename)
            profile_image.save(save_path)
            db_path_str = f"uploads/avatars/{unique_filename}"
            
            update_query += ", profile_image = ?"
            params.append(db_path_str)

        update_query += " WHERE id = ?"
        params.append(session['user_id'])

        conn = sqlite3.connect(db_pathusers)
        conn.execute(update_query, params)
        conn.commit()
        conn.close()

        flash('Profile updated successfully!')
        return redirect(url_for('profile'))

    return render_template("update_profile.html", username=username, email=email, profile_image=profile_image)

def encrypt_username(username):
    return hashlib.sha256(username.encode()).hexdigest()

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        uniq_id = encrypt_username(username)
        hashed_password = generate_password_hash(password)
        try:
            with sqlite3.connect(db_pathusers) as db:
                cursor = db.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    return render_template('register.html', error="User already exists")
                query = """ INSERT INTO users (username, email, password, uniq_id) VALUES (?, ?, ?, ?) """
                cursor.execute(query, (username, email, hashed_password, uniq_id))
                db.commit()
                session['user_id'] = cursor.lastrowid

            return redirect(url_for('mainpage'))

        except sqlite3.IntegrityError:
            return "Ошибка: пользователь с таким email или именем уже существует!"

    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            with sqlite3.connect(db_pathusers) as db:
                cursor = db.cursor()
                cursor.execute("SELECT id, username, password FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                if user and check_password_hash(user[2], password):
                    session['user_id'] = user[0]
                    username = user[1]
                    return redirect(url_for('mainpage', username=username))
                else:
                   return render_template("login.html", error="Invalid credentials") 

        except sqlite3.Error:
            return "Ошибка при подключении к базе данных"
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('mainpage'))

def get_post(post_id):
    try:
        # Подключаемся к базе постов и получаем данные поста
        conn_posts = sqlite3.connect(db_pathpost)
        conn_posts.row_factory = sqlite3.Row
        post = conn_posts.execute(
            '''
            SELECT * FROM posts WHERE id = ?
            ''', (post_id,)
        ).fetchone()
        conn_posts.close()

        if post is None:
            abort(404)  # Пост не найден

        # Подключаемся к базе пользователей, чтобы получить имя автора
        conn_users = sqlite3.connect(db_pathusers)
        conn_users.row_factory = sqlite3.Row
        user = conn_users.execute(
            '''
            SELECT username FROM users WHERE uniq_id = ?
            ''', (post['user_uniq_id'],)
        ).fetchone()
        conn_users.close()

        # Добавляем имя автора к посту
        post_data = dict(post)
        post_data['author'] = user['username'] if user else 'Unknown'

        return post_data

    except sqlite3.Error as e:
        abort(500, description=f"Database error: {e}")

@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)  # Получаем пост по ID
    username = None
    profile_image = None
    comments = []

    with sqlite3.connect(db_pathpost) as conn_comments, sqlite3.connect(db_pathusers) as conn_users:
        conn_comments.row_factory = sqlite3.Row
        cursor_comments = conn_comments.cursor()
        
        # Получаем комментарии для поста
        cursor_comments.execute('SELECT user_id, comment_content FROM comments WHERE post_id = ?', (post_id,))
        raw_comments = cursor_comments.fetchall()

        conn_users.row_factory = sqlite3.Row
        cursor_users = conn_users.cursor()

        for row in raw_comments:
            user_id = row['user_id']
            
            # Получаем актуальное имя пользователя по user_id
            cursor_users.execute('SELECT username FROM users WHERE uniq_id = ?', (user_id,))
            user = cursor_users.fetchone()
            author = user['username'] if user else 'Unknown'

            comments.append({
                'author': author,
                'comment_content': row['comment_content']
            })

    # Если пользователь авторизован, получаем его данные
    if 'user_id' in session:
        conn = sqlite3.connect(db_pathusers)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT username, profile_image FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        if user:
            username = user['username']
            profile_image = user['profile_image']  # Получаем аватар пользователя

    return render_template('post.html', post=post, username=username, profile_image=profile_image, comments=comments)

@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    if 'user_id' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id']
    liked = None
    if 'user_id' in session:
        with sqlite3.connect(db_pathpost) as db:
            cursor = db.cursor()

            # Check if the user has already liked the post
            cursor.execute("SELECT * FROM post_likes WHERE user_id = ? AND post_id = ? ", (user_id, post_id,))
            like = cursor.fetchone()

            if like:
                # If the user has already liked the post, remove the like
                cursor.execute("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
                cursor.execute("UPDATE posts SET like_count = like_count - 1 WHERE id = ?", (post_id,))
                db.commit()
                liked = True
            else:
                # If the user hasn't liked the post, add the like
                cursor.execute("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
                cursor.execute("UPDATE posts SET like_count = like_count + 1 WHERE id = ?", (post_id,))
                db.commit()
                liked = False

            return redirect(url_for('mainpage', liked=liked, user_id=user_id))  # Redirect back to the main page

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Перенаправление на страницу входа, если не авторизован

    # Получаем информацию о текущем пользователе
    try:
        conn = sqlite3.connect(db_pathusers)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT username, uniq_id FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()

        if not user:
            flash('User not found. Please log in again.')
            return redirect(url_for('logout'))

        author = user['username']
        user_id = user['uniq_id']

    except sqlite3.Error as e:
        print(f"Database error (users): {e}")
        flash('Error retrieving user information.')
        return redirect(url_for('post', post_id=post_id))

    # Получаем содержимое комментария из формы
    comment_content = request.form.get('comment_content', '').strip()
    if not comment_content:
        flash('Comment cannot be empty.')
        return redirect(url_for('post', post_id=post_id))

    # Сохраняем комментарий в базу данных
    try:
        conn = sqlite3.connect(db_pathpost)
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO comments (post_id, comment_content, author, user_id)
            VALUES (?, ?, ?, ?)
            ''',
            (post_id, comment_content, author, user_id)
        )
        conn.commit() 
        conn.close()
        flash('Comment created successfully!')
    except sqlite3.Error as e:
        print(f"Database error (comments): {e}")
        flash('Error saving comment.')

    return redirect(url_for('post', post_id=post_id))

@app.route('/create', methods=('GET', 'POST'))
def create():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash('You must be logged in to create a post!')
        return redirect(url_for('login'))

    username = None
    uniq_id = None
    author = None
    profile_image = None
    if 'user_id' in session:
        # Получаем имя пользователя и uniq_id из базы данных
        conn = sqlite3.connect(db_pathusers)
        cursor = conn.cursor()
        cursor.execute("SELECT username, uniq_id, profile_image FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        if user:
            username = user[0]
            profile_image = user[2]
            uniq_id = user[1]
    author = username
    user_uniq_id = uniq_id
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content'].replace("\r\n", "\n")  # Нормализуем переносы строк
        description = request.form['description']
        post_image = request.files['image']

        # Проверяем данные
        if not title:
            flash('Title is required!')
        elif not content:
            flash('Content is required!')
        else:
            db_path_str = None
            if post_image and post_image.filename:
                filename = secure_filename(post_image.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', unique_filename)
                post_image.save(save_path)
                db_path_str = f"uploads/posts/{unique_filename}"

            # Сохраняем пост в базу данных
            conn = sqlite3.connect(db_pathpost)
            conn.execute(
                'INSERT INTO posts (title, content, description, user_uniq_id, post_image, author) VALUES (?, ?, ?, ?, ?, ?)',
                (title, content, description, user_uniq_id, db_path_str, author)
            )

            conn.commit()
            conn.close()

            flash('Post created successfully!')
            return redirect(url_for('mainpage'))

    return render_template('create.html', username=username, profile_image = profile_image)

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    post = get_post(id)
    if not post:
        flash('Post not found!')
        return redirect(url_for('mainpage'))

    profile_image = None
    username = None
    uniq_id = None

    if 'user_id' not in session:
        flash('You must be logged in to edit a post!')
        return redirect(url_for('login'))

    conn = sqlite3.connect(db_pathusers)
    cursor = conn.cursor()
    cursor.execute("SELECT username, profile_image, uniq_id FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()

    if user:
        username = user[0]
        profile_image = user[1]
        uniq_id = user[2]

    

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content'].replace("\r\n", "\n")  # Нормализуем переносы строк
        post_image = request.files.get('image')

        if not title:
            flash('Title is required!')
        else:
            conn = sqlite3.connect(db_pathpost)
            cursor = conn.cursor()
            
            # Если изображение было загружено, обновляем его
            if post_image and post_image.filename:
                filename = secure_filename(post_image.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', unique_filename)
                post_image.save(save_path)
                db_path_str = f"uploads/posts/{unique_filename}"

                cursor.execute('''
                    UPDATE posts 
                    SET title = ?, content = ?, post_image = ?, last_modified = ? 
                    WHERE id = ?
                ''', (title, content, db_path_str, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id))
            else:
                cursor.execute('''
                    UPDATE posts 
                    SET title = ?, content = ?, last_modified = ? 
                    WHERE id = ?
                ''', (title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id))

            conn.commit()
            conn.close()

            flash('Post updated successfully!')
            return redirect(url_for('mainpage'))

    return render_template('edit.html', post=post, username=username, profile_image=profile_image)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    post = get_post(id)
    conn = sqlite3.connect(db_pathpost)
    cursor = conn.cursor()
    
    # Удаляем лайки, комментарии и пост
    cursor.execute('DELETE FROM post_likes WHERE post_id = ?', (id,))
    cursor.execute('DELETE FROM comments WHERE post_id = ?', (id,))
    cursor.execute('DELETE FROM posts WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()
    
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('mainpage'))


if __name__ == "__main__":
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', port=int(os.environ.get('PORT', 1488)))
