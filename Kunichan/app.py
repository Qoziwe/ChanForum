from flask import Flask, render_template, request, session, redirect, url_for, flash
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
db_pathuserfriends = os.path.join(BASE_DIR, 'db', 'databaseusers.db')
Error = None


@app.template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8')

@app.route("/")
def mainpage():
    try:
        # Подключаемся к базе постов и получаем список постов
        conn_posts = sqlite3.connect(db_pathpost)
        conn_posts.row_factory = sqlite3.Row
        posts = conn_posts.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
        conn_posts.close()

        # Преобразуем данные постов в список словарей
        post_list = [dict(post) for post in posts]

        # Получаем уникальные идентификаторы пользователей из постов
        user_ids = {post['user_uniq_id'] for post in post_list}

        # Подключаемся к базе пользователей, чтобы получить имена авторов
        conn_users = sqlite3.connect(db_pathusers)
        conn_users.row_factory = sqlite3.Row
        users = conn_users.execute(
            f"SELECT uniq_id, username FROM users WHERE uniq_id IN ({','.join(['?'] * len(user_ids))})",
            tuple(user_ids)
        ).fetchall()
        conn_users.close()

        # Создаём словарь {uniq_id: username} для быстрого поиска
        user_dict = {user['uniq_id']: user['username'] for user in users}

        # Добавляем имена авторов к каждому посту
        for post in post_list:
            post['author'] = user_dict.get(post['user_uniq_id'], 'Unknown')

        # Проверяем, авторизован ли пользователь
        username = None
        profile_image = None
        if 'user_id' in session:
            conn_users = sqlite3.connect(db_pathusers)
            conn_users.row_factory = sqlite3.Row
            user = conn_users.execute(
                "SELECT username, profile_image FROM users WHERE id = ?",
                (session['user_id'],)
            ).fetchone()
            conn_users.close()

            if user:
                username = user['username']
                profile_image = user['profile_image']

        return render_template("mainpage.html", username=username, profile_image=profile_image, posts=post_list)

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
    
    
    if 'user_id' in session:
        with sqlite3.connect(db_pathusers) as db:
            cursor = db.cursor()
            cursor.execute("SELECT username, profile_image FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                username = user[0]
                profile_image = user[1] if user[1] else None  # Изображение профиля
                return render_template("profile.html", username=username, profile_image=profile_image)
    flash('User not logged in. Please login.')
    return redirect(url_for('login'))

@app.route('/unknownuser/<int:post_id>')
def unknownuser(post_id):
    # Получаем user_uniq_id автора поста
    conn1 = sqlite3.connect(db_pathpost)
    cursor1 = conn1.cursor()
    cursor1.execute("SELECT user_uniq_id FROM posts WHERE id = ?", (post_id,))
    post_author_id = cursor1.fetchone()
    conn1.close()
    
    if not post_author_id:
        abort(404)  # Пост не найден

    post_author_id = post_author_id[0]  # Извлекаем user_uniq_id из результата

    # Получаем информацию об авторе поста
    conn2 = sqlite3.connect(db_pathusers)
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT username, profile_image FROM users WHERE uniq_id = ?", (post_author_id,))
    author_data = cursor2.fetchone()
    conn2.close()

    if not author_data:
        abort(404)  # Автор поста не найден

    author_username, author_image = author_data

    # Данные о текущем пользователе (если он вошел в систему)
    username = None
    profile_image = None
    current_user_id = session.get('user_id')  # Получаем текущего пользователя из сессии

    if current_user_id:
        conn = sqlite3.connect(db_pathusers)
        cursor = conn.cursor()
        cursor.execute("SELECT username, profile_image, uniq_id FROM users WHERE id = ?", (current_user_id,))
        logged_in_user = cursor.fetchone()
        conn.close()
        
        if logged_in_user:
            username, profile_image, logged_in_uniq_id = logged_in_user
            
            # Если текущий пользователь — автор поста, перенаправляем в профиль
            if post_author_id == logged_in_uniq_id:
                return redirect(url_for('profile'))

    return render_template('unknownuser.html', 
                           author_username=author_username,
                           author_image=author_image,
                           username=username,
                           profile_image=profile_image)

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

        # Подключаемся к базе лайков
        conn_likes = sqlite3.connect(db_pathpost)
        conn_likes.row_factory = sqlite3.Row

        # Получаем количество лайков
        likes_count = conn_likes.execute(
            '''
            SELECT COUNT(*) AS total_likes FROM likes WHERE post_id = ?
            ''', (post_id,)
        ).fetchone()['total_likes']

        # Проверяем, лайкнул ли текущий пользователь пост
        user_liked = False
        if 'user_id' in session:
            user_liked = conn_likes.execute(
                '''
                SELECT 1 FROM likes WHERE post_id = ? AND user_id = ?
                ''', (post_id, session['user_id'])
            ).fetchone() is not None

        conn_likes.close()

        # Добавляем информацию о лайках в данные поста
        post_data['likes_count'] = likes_count
        post_data['user_liked'] = user_liked

        return post_data

    except sqlite3.Error as e:
        abort(500, description=f"Database error: {e}")


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)  # Получаем пост по ID
    username = None
    profile_image = None
    if 'user_id' in session:
        conn = sqlite3.connect(db_pathusers)
        cursor = conn.cursor()
        cursor.execute("SELECT username, profile_image FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        if user:
            username = user[0]
            profile_image = user[1]  # Получаем аватар пользователя
    
    return render_template('post.html', post=post, username=username, profile_image=profile_image)




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
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('mainpage'))


if __name__ == "__main__":
    app.run(debug=True, port=5502)
