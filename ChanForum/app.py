from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
import uuid
import re
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ===== ШАГ 1: Безопасный SECRET_KEY (VULN-001) =====
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set! "
        "Generate one with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    )
app.secret_key = secret_key

# ===== ШАГ 2: CSRF-защита (VULN-002) =====
csrf = CSRFProtect(app)

# ===== ШАГ 9: Rate Limiting (VULN-009) =====
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# ===== ШАГ 11: Безопасность сессий (VULN-011) =====
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# ===== ШАГ 4: Ограничение размера загружаемых файлов (VULN-018) =====
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
db_pathpost = os.path.join(BASE_DIR, 'db', 'databasepost.db')
db_pathusers = os.path.join(BASE_DIR, 'db', 'databaseusers.db')

# ===== ШАГ 20: Логирование (VULN-025, VULN-027) =====
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'chanforum.log'),
    maxBytes=1024 * 1024,  # 1 MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)

# Console handler для dev
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(console_handler)


# ===== ШАГ 4: Валидация файлов (VULN-004, VULN-020) =====
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    """Проверяет расширение файла."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(file_stream):
    """Проверяет magic bytes файла для подтверждения, что это изображение."""
    header = file_stream.read(12)
    file_stream.seek(0)

    # PNG
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    # JPEG
    if header[:3] == b'\xff\xd8\xff':
        return True
    # GIF
    if header[:6] in (b'GIF87a', b'GIF89a'):
        return True
    # WebP
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return True

    return False


def save_uploaded_image(file, subfolder):
    """Безопасно сохраняет загруженное изображение. Возвращает путь для БД или None."""
    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        flash('Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WebP')
        return None

    if not validate_image(file.stream):
        flash('File does not appear to be a valid image.')
        return None

    filename = secure_filename(file.filename)
    if not filename:
        flash('Invalid filename.')
        return None

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    save_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)

    # Создать каталог если не существует
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, unique_filename)
    try:
        file.save(save_path)
    except OSError as e:
        logger.error(f"Failed to save uploaded file: {e}")
        flash('Error saving file. Please try again.')
        return None

    return f"uploads/{subfolder}/{unique_filename}"


# ===== ШАГ 5: Безопасный uniq_id (VULN-005) =====
def generate_unique_id():
    """Генерирует криптографически стойкий уникальный идентификатор."""
    return uuid.uuid4().hex


# ===== ШАГ 8: Валидация паролей (VULN-008) =====
def validate_password(password):
    """Проверяет пароль на минимальные требования безопасности."""
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character.")
    return errors


# ===== ШАГ 16: Валидация входных данных (VULN-016) =====
def validate_username(username):
    """Валидирует username."""
    if not username or len(username) < 3 or len(username) > 25:
        return "Username must be between 3 and 25 characters."
    if not re.match(r'^[a-zA-Z0-9_\-а-яА-ЯёЁ]+$', username):
        return "Username can only contain letters, numbers, underscores, and hyphens."
    return None


def validate_email(email):
    """Базовая валидация email."""
    if not email or len(email) > 255:
        return "Invalid email address."
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
        return "Invalid email format."
    return None


def validate_post_content(title, content, description=None):
    """Валидирует содержимое поста."""
    errors = []
    if not title or len(title) > 200:
        errors.append("Title must be between 1 and 200 characters.")
    if not content or len(content) > 50000:
        errors.append("Content must be between 1 and 50,000 characters.")
    if description and len(description) > 500:
        errors.append("Description must not exceed 500 characters.")
    return errors


# ===== ШАГ 10: Security Headers (VULN-010, VULN-029) =====
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "frame-ancestors 'none';"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    return response


# ===== ШАГ 19: HTTPS редирект для продакшена (VULN-023) =====
@app.before_request
def redirect_to_https():
    if os.environ.get('FLASK_ENV') == 'production' and not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)


# ===== ШАГ 4: Обработчик 413 (VULN-018) =====
@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 5 MB.')
    return redirect(request.referrer or url_for('mainpage')), 413


# ===== ШАГ 6: Кастомные страницы ошибок (VULN-006) =====
@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', error_code=404, error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('base.html', error_code=500, error_message="An internal error occurred"), 500


# ===== МАРШРУТЫ =====

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
        # ===== ШАГ 6: Не раскрываем детали ошибки (VULN-006) =====
        logger.error(f"Database error in mainpage: {e}")
        abort(500, description="An internal error occurred. Please try again later.")

      
@app.route('/friends', methods=['GET', 'POST'])
def friends():
    username = None
    profile_image = None
    users_list = []

    if 'user_id' in session:
        user_id = session['user_id']
        # ===== ШАГ 15: Унифицировать DB-соединения через with (VULN-015, VULN-019) =====
        with sqlite3.connect(db_pathusers) as conn:
            cursor = conn.cursor()
            user = cursor.execute('SELECT username, profile_image FROM users WHERE id = ?', (user_id,)).fetchone()

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
    is_friend = False

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

    if 'user_id' not in session:
        return redirect(url_for('login'))

    # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
    with sqlite3.connect(db_pathusers) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, profile_image, uniq_id FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

        if user:
            username = user[0]
            profile_image = user[1]
            uniq_id = user[2]

    if uniq_id:
        with sqlite3.connect(db_pathpost) as conn:
            conn.row_factory = sqlite3.Row
            posts = conn.execute(
                'SELECT * FROM posts WHERE user_uniq_id = ? ORDER BY id DESC', 
                (uniq_id,)
            ).fetchall()

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
        # ===== ШАГ 6: Логируем, но не раскрываем пользователю (VULN-006) =====
        logger.error(f"Database error in profile: {e}")
        flash('An error occurred. Please try again.')
        return redirect(url_for('login'))

    return render_template("profile.html", username=username, profile_image=profile_image, liked_posts=liked_posts)


@app.route('/profile/<string:uniq_id>')
def unknown_profile(uniq_id):
    # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
    with sqlite3.connect(db_pathusers) as conn:
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

            return render_template('profile.html', unknowninfo={
                'username': username,
                'profile_image': profile_image,
                'uniq_id': uniq_id
            }, is_friend=is_friend)

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
            abort(404)

        post_author_id = post_author_id[0]

        # Проверяем текущего пользователя
        current_username = None
        current_profile_image = None
        current_user_id = session.get('user_id')
        uniq_id = None
        is_friend = False

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
                            cursor_users.execute(
                                "INSERT INTO user_friends (user_id, friend_id) VALUES (?, ?)",
                                (logged_in_uniq_id, post_author_id)
                            )
                            conn_users.commit()
                            flash('User has been added to your friends.')
                            is_friend = True
                            logger.info(f"Friend added: user={logged_in_uniq_id} -> friend={post_author_id}")
                        except sqlite3.Error as e:
                            # ===== ШАГ 6: Не раскрываем детали ошибки (VULN-006) =====
                            logger.error(f"Database error adding friend: {e}")
                            flash("An error occurred. Please try again.")

        # Получаем информацию об авторе поста
        with sqlite3.connect(db_pathusers) as conn_users:
            cursor_users = conn_users.cursor()
            cursor_users.execute(
                "SELECT username, profile_image FROM users WHERE uniq_id = ?", 
                (post_author_id,)
            )
            author_data = cursor_users.fetchone()
        
        if not author_data:
            abort(404)

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
        logger.error(f"Database error in unknownuser: {e}")
        abort(500, description="An internal error occurred. Please try again later.")


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user_id' not in session:
        flash('User not logged in. Please login.')
        return redirect(url_for('login'))
    
    # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
    with sqlite3.connect(db_pathusers) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, email, profile_image FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

    if not user:
        flash('User not found.')
        return redirect(url_for('profile'))

    username, email, profile_image = user

    if request.method == 'POST':
        new_username = request.form.get('username', username)
        new_email = request.form.get('email', email)
        new_password = request.form.get('password')
        profile_image_file = request.files.get('profile_image')

        # ===== ШАГ 16: Серверная валидация входных данных (VULN-016) =====
        username_error = validate_username(new_username)
        if username_error:
            flash(username_error)
            return render_template("update_profile.html", username=username, email=email, profile_image=profile_image)

        email_error = validate_email(new_email)
        if email_error:
            flash(email_error)
            return render_template("update_profile.html", username=username, email=email, profile_image=profile_image)

        update_query = "UPDATE users SET username = ?, email = ?"
        params = [new_username, new_email]

        # ===== ШАГ 8: Валидация пароля при обновлении (VULN-008) =====
        if new_password:
            password_errors = validate_password(new_password)
            if password_errors:
                for error in password_errors:
                    flash(error)
                return render_template("update_profile.html", username=username, email=email, profile_image=profile_image)
            update_query += ", password = ?"
            params.append(generate_password_hash(new_password))

        # ===== ШАГ 4: Безопасная загрузка файлов (VULN-004) =====
        if profile_image_file and profile_image_file.filename:
            db_path_str = save_uploaded_image(profile_image_file, 'avatars')
            if db_path_str:
                update_query += ", profile_image = ?"
                params.append(db_path_str)

        update_query += " WHERE id = ?"
        params.append(session['user_id'])

        with sqlite3.connect(db_pathusers) as conn:
            conn.execute(update_query, params)
            conn.commit()

        flash('Profile updated successfully!')
        logger.info(f"Profile updated: user_id={session['user_id']}, ip={request.remote_addr}")
        return redirect(url_for('profile'))

    return render_template("update_profile.html", username=username, email=email, profile_image=profile_image)


@app.route("/register", methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # ===== ШАГ 16: Серверная валидация (VULN-016) =====
        username_error = validate_username(username)
        if username_error:
            flash(username_error)
            return render_template('register.html')

        email_error = validate_email(email)
        if email_error:
            flash(email_error)
            return render_template('register.html')

        # ===== ШАГ 8: Валидация пароля (VULN-008) =====
        password_errors = validate_password(password)
        if password_errors:
            for error in password_errors:
                flash(error)
            return render_template('register.html')
        
        # ===== ШАГ 5: UUID4 вместо SHA-256 (VULN-005) =====
        uniq_id = generate_unique_id()
        hashed_password = generate_password_hash(password)
        try:
            with sqlite3.connect(db_pathusers) as db:
                cursor = db.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    # ===== ШАГ 17: Не раскрываем, зарегистрирован ли email (VULN-017) =====
                    flash("Registration failed. Please try with different credentials.")
                    return render_template('register.html')
                query = """ INSERT INTO users (username, email, password, uniq_id) VALUES (?, ?, ?, ?) """
                cursor.execute(query, (username, email, hashed_password, uniq_id))
                db.commit()
                session.permanent = True
                session['user_id'] = cursor.lastrowid

            logger.info(f"New user registered: username={username}, ip={request.remote_addr}")
            return redirect(url_for('mainpage'))

        except sqlite3.IntegrityError:
            # ===== ШАГ 17: Унифицированный ответ (VULN-017) =====
            flash("Registration failed. Please try with different credentials.")
            return render_template('register.html')

    return render_template("register.html")


@app.route("/login", methods=['GET', 'POST'])
@limiter.limit("5 per minute")
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
                    session.permanent = True
                    session['user_id'] = user[0]
                    username = user[1]
                    # ===== ШАГ 20: Логирование успешного логина (VULN-025) =====
                    logger.info(f"Successful login: email={email}, ip={request.remote_addr}")
                    return redirect(url_for('mainpage', username=username))
                else:
                    # ===== ШАГ 20: Логирование неудачной попытки (VULN-025) =====
                    logger.warning(f"Failed login attempt: email={email}, ip={request.remote_addr}")
                    return render_template("login.html", error="Invalid credentials") 

        except sqlite3.Error as e:
            logger.error(f"Database error in login: {e}")
            flash("An error occurred. Please try again.")
            return render_template("login.html")
    
    return render_template("login.html")


# ===== ШАГ 13: Logout через POST (VULN-013) =====
@app.route("/logout", methods=['POST'])
def logout():
    logger.info(f"User logged out: user_id={session.get('user_id')}, ip={request.remote_addr}")
    session.pop('user_id', None)
    return redirect(url_for('mainpage'))


def get_post(post_id):
    try:
        # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
        with sqlite3.connect(db_pathpost) as conn_posts:
            conn_posts.row_factory = sqlite3.Row
            post = conn_posts.execute(
                'SELECT * FROM posts WHERE id = ?', (post_id,)
            ).fetchone()

        if post is None:
            abort(404)

        with sqlite3.connect(db_pathusers) as conn_users:
            conn_users.row_factory = sqlite3.Row
            user = conn_users.execute(
                'SELECT username FROM users WHERE uniq_id = ?',
                (post['user_uniq_id'],)
            ).fetchone()

        # Добавляем имя автора к посту
        post_data = dict(post)
        post_data['author'] = user['username'] if user else 'Unknown'

        return post_data

    except sqlite3.Error as e:
        logger.error(f"Database error in get_post: {e}")
        abort(500, description="An internal error occurred. Please try again later.")


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
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
        # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
        with sqlite3.connect(db_pathusers) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT username, profile_image FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                username = user['username']
                profile_image = user['profile_image']

    return render_template('post.html', post=post, username=username, profile_image=profile_image, comments=comments)


@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    liked = None
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

        return redirect(url_for('mainpage', liked=liked, user_id=user_id))


@app.route('/comment/<int:post_id>', methods=['POST'])
@limiter.limit("20 per hour")
def comment(post_id):
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Получаем информацию о текущем пользователе
    try:
        # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
        with sqlite3.connect(db_pathusers) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT username, uniq_id FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()

        if not user:
            flash('User not found. Please log in again.')
            return redirect(url_for('logout_get_redirect'))

        author = user['username']
        user_id = user['uniq_id']

    except sqlite3.Error as e:
        logger.error(f"Database error in comment (users): {e}")
        flash('Error retrieving user information.')
        return redirect(url_for('post', post_id=post_id))

    # Получаем содержимое комментария из формы
    comment_content = request.form.get('comment_content', '').strip()
    if not comment_content:
        flash('Comment cannot be empty.')
        return redirect(url_for('post', post_id=post_id))

    # ===== ШАГ 16: Валидация длины комментария (VULN-016) =====
    if len(comment_content) > 5000:
        flash('Comment is too long. Maximum 5000 characters.')
        return redirect(url_for('post', post_id=post_id))

    # Сохраняем комментарий в базу данных
    try:
        with sqlite3.connect(db_pathpost) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO comments (post_id, comment_content, author, user_id)
                VALUES (?, ?, ?, ?)
                ''',
                (post_id, comment_content, author, user_id)
            )
            conn.commit()
        flash('Comment created successfully!')
    except sqlite3.Error as e:
        logger.error(f"Database error in comment (comments): {e}")
        flash('Error saving comment.')

    return redirect(url_for('post', post_id=post_id))


@app.route('/create', methods=('GET', 'POST'))
@limiter.limit("10 per hour")
def create():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash('You must be logged in to create a post!')
        return redirect(url_for('login'))

    username = None
    uniq_id = None
    author = None
    profile_image = None

    # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
    with sqlite3.connect(db_pathusers) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, uniq_id, profile_image FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if user:
            username = user[0]
            profile_image = user[2]
            uniq_id = user[1]

    author = username
    user_uniq_id = uniq_id

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content'].replace("\r\n", "\n")
        description = request.form['description']
        post_image = request.files.get('image')

        # ===== ШАГ 16: Серверная валидация контента (VULN-016) =====
        content_errors = validate_post_content(title, content, description)
        if content_errors:
            for err in content_errors:
                flash(err)
            return render_template('create.html', username=username, profile_image=profile_image)

        # ===== ШАГ 4: Безопасная загрузка файлов (VULN-004) =====
        db_path_str = None
        if post_image and post_image.filename:
            db_path_str = save_uploaded_image(post_image, 'posts')

        # Сохраняем пост в базу данных
        with sqlite3.connect(db_pathpost) as conn:
            conn.execute(
                'INSERT INTO posts (title, content, description, user_uniq_id, post_image, author) VALUES (?, ?, ?, ?, ?, ?)',
                (title, content, description, user_uniq_id, db_path_str, author)
            )
            conn.commit()

        flash('Post created successfully!')
        logger.info(f"Post created: user_id={session['user_id']}, title={title[:50]}, ip={request.remote_addr}")
        return redirect(url_for('mainpage'))

    return render_template('create.html', username=username, profile_image=profile_image)


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

    # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
    with sqlite3.connect(db_pathusers) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, profile_image, uniq_id FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    username = user[0]
    profile_image = user[1]
    uniq_id = user[2]

    # ===== ШАГ 3: Проверка владельца поста (VULN-003) =====
    if post['user_uniq_id'] != uniq_id:
        flash('You can only edit your own posts!')
        logger.warning(f"Unauthorized edit attempt: user_id={session['user_id']} tried to edit post_id={id}, ip={request.remote_addr}")
        return redirect(url_for('mainpage'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content'].replace("\r\n", "\n")
        post_image = request.files.get('image')

        # ===== ШАГ 16: Валидация контента (VULN-016) =====
        if not title or len(title) > 200:
            flash('Title must be between 1 and 200 characters.')
        else:
            with sqlite3.connect(db_pathpost) as conn:
                cursor = conn.cursor()
                
                # ===== ШАГ 4: Безопасная загрузка файлов (VULN-004) =====
                if post_image and post_image.filename:
                    db_path_str = save_uploaded_image(post_image, 'posts')
                    if db_path_str:
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
                else:
                    cursor.execute('''
                        UPDATE posts 
                        SET title = ?, content = ?, last_modified = ? 
                        WHERE id = ?
                    ''', (title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id))

                conn.commit()

            flash('Post updated successfully!')
            logger.info(f"Post edited: post_id={id}, user_id={session['user_id']}, ip={request.remote_addr}")
            return redirect(url_for('mainpage'))

    return render_template('edit.html', post=post, username=username, profile_image=profile_image)


@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    post = get_post(id)

    # ===== ШАГ 3: Проверка владельца поста (VULN-003) =====
    with sqlite3.connect(db_pathusers) as conn_users:
        cursor = conn_users.cursor()
        cursor.execute("SELECT uniq_id FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()

    if not user or post['user_uniq_id'] != user[0]:
        flash('You can only delete your own posts!')
        logger.warning(f"Unauthorized delete attempt: user_id={session['user_id']} tried to delete post_id={id}, ip={request.remote_addr}")
        return redirect(url_for('mainpage'))

    # ===== ШАГ 15: with вместо ручного close (VULN-015) =====
    with sqlite3.connect(db_pathpost) as conn:
        cursor = conn.cursor()
        # Удаляем лайки, комментарии и пост
        cursor.execute('DELETE FROM post_likes WHERE post_id = ?', (id,))
        cursor.execute('DELETE FROM comments WHERE post_id = ?', (id,))
        cursor.execute('DELETE FROM posts WHERE id = ?', (id,))
        conn.commit()
    
    flash('"{}" was successfully deleted!'.format(post['title']))
    logger.info(f"Post deleted: post_id={id}, user_id={session['user_id']}, ip={request.remote_addr}")
    return redirect(url_for('mainpage'))


# ===== ШАГ 21: Защита DEBUG режима (VULN-026) =====
if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    if debug_mode:
        print("WARNING: Running in DEBUG mode! Do NOT use this in production!")
    app.run(debug=debug_mode, port=int(os.environ.get('PORT', 5000)))
