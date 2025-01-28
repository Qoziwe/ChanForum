from flask import Flask, jsonify, render_template, request, session, redirect, url_for, flash
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from datetime import datetime
import base64
import sqlite3
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'yourmom'  # your mom

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_pathpost = os.path.join(BASE_DIR, 'db', 'databasepost.db')
db_pathusers = os.path.join(BASE_DIR, 'db', 'databaseusers.db')
db_pathuserfriends = os.path.join(BASE_DIR, 'db', 'databasefriends.db')
Error = None


@app.template_filter('b64encode')
def b64encode_filter(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

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
                    "SELECT username, profile_image, friend_id FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()

                if user:
                    username = user['username']
                    profile_image = user['profile_image']
                    # Получаем friend_id текущего пользователя
                    friend_ids = user['friend_id']
                    if friend_ids:
                        # Если есть друзья, извлекаем их uniq_id
                        friend_ids_list = friend_ids.split(',')
                        with sqlite3.connect(db_pathusers) as conn_users_friends:
                            conn_users_friends.row_factory = sqlite3.Row
                            friends_data = conn_users_friends.execute(
                                f"SELECT uniq_id, username, profile_image FROM users WHERE uniq_id IN ({','.join(['?'] * len(friend_ids_list))})",
                                tuple(friend_ids_list)
                            ).fetchall()
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
                query = f"SELECT id, title, content FROM posts WHERE id IN ({placeholders}) ORDER BY id DESC"
                cursor.execute(query, liked_post_ids)
                liked_posts_data = cursor.fetchall()

                # Convert to list of dictionaries
                liked_posts = [
                    {"id": row[0], "title": row[1], "content": row[2]}
                    for row in liked_posts_data
                ]

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        flash('Error with the database.')
        return redirect(url_for('login'))

    return render_template("profile.html", username=username, profile_image=profile_image, liked_posts=liked_posts)


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
                    "SELECT username, profile_image, uniq_id, friend_id FROM users WHERE id = ?", 
                    (current_user_id,)
                )
                logged_in_user = cursor_users.fetchone()

                if logged_in_user:
                    current_username, current_profile_image, logged_in_uniq_id, friend_ids = logged_in_user
                    uniq_id = logged_in_user[2]

                    # Если текущий пользователь — автор поста, перенаправляем в профиль
                    if post_author_id == logged_in_uniq_id:
                        return redirect(url_for('profile'))

                    # Проверяем, является ли автор поста другом текущего пользователя
                    is_friend = post_author_id in friend_ids.split(',') if friend_ids else False

                    # Если метод POST, пытаемся добавить автора поста в друзья
                    if request.method == 'POST' and not is_friend:
                        try:
                            # Обновляем поле friend_id для текущего пользователя
                            friend_ids = friend_ids.split(',') if friend_ids else []
                            friend_ids.append(post_author_id)  # Добавляем uniq_id как строку
                            updated_friend_ids = ','.join(friend_ids)

                            cursor_users.execute(
                                "UPDATE users SET friend_id = ? WHERE id = ?",
                                (updated_friend_ids, current_user_id)
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
            params.append(new_password)

        if profile_image:
            profile_image_data = profile_image.read()
            update_query += ", profile_image = ?"
            params.append(profile_image_data)

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
        try:
            with sqlite3.connect(db_pathusers) as db:
                cursor = db.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    return render_template('register.html', error=Error)
                cursor = db.cursor()
                query = """ INSERT INTO users (username, email, password, uniq_id) VALUES (?, ?, ?, ?) """
                cursor.execute(query, (username, email, password, uniq_id))
                db.commit()
                session['user_id'] = cursor.lastrowid

            return redirect(url_for('mainpage'))

        except sqlite3.IntegrityError:
            return "Ошибка: пользователь с таким email уже существует!"

    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            with sqlite3.connect(db_pathusers) as db:
                cursor = db.cursor()
                cursor.execute("SELECT id, username FROM users WHERE email = ? AND password = ?", (email, password))
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user[0]
                    username = user[1]
                    return redirect(url_for('mainpage', username=username))
                else:
                   return render_template("login.html", error=Error) 

        except sqlite3.IntegrityError:
            return "Ошибка: пользователь с таким email уже существует!"
    
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






#likes 

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
            # Преобразуем изображение в бинарные данные
            image_blob = post_image.read()

            # Сохраняем пост в базу данных
            conn = sqlite3.connect(db_pathpost)
            conn.execute(
                'INSERT INTO posts (title, content, description, user_uniq_id, post_image, author) VALUES (?, ?, ?, ?, ?, ?)',
                (title, content, description, user_uniq_id, image_blob, author)
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
                image_blob = post_image.read()
                cursor.execute('''
                    UPDATE posts 
                    SET title = ?, content = ?, post_image = ?, last_modified = ? 
                    WHERE id = ?
                ''', (title, content, image_blob, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id))
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
    app.run(debug=True, port=1488)
