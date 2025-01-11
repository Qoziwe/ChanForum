from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'yourmom'  # your mom

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'db', 'database.db')

@app.route("/")
def mainpage():
    if 'user_id' in session:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                username = user[0]
                return render_template("mainpage.html", username=username)
    return render_template("mainpage.html", username=None)

@app.route('/profile')
def profile():
    if 'user_id' in session:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT username, email FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()

            if user:
                username = user[0]
                email = user[1]
                return render_template("profile.html", username=username, email=email)
            else:
                return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route("/edit")
def edit_profile():
    if 'user_id' in session:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT username, email FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                return render_template("edit.html", username=user[0], email=user[1])
    return redirect(url_for('login'))

@app.route("/update_profile", methods=["POST"])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    profile_picture = request.files.get('profile_picture')
    try:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, session['user_id']))
            db.commit()
            if email and email.strip():
                cursor.execute("UPDATE users SET email = ? WHERE id = ?", (email.strip(), session['user_id']))
            if password and password.strip():
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (password.strip(), session['user_id']))
            if profile_picture:
                filename = f"user_{session['user_id']}_{profile_picture.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_picture.save(filepath)
                cursor.execute("UPDATE users SET profile_picture = ? WHERE id = ?", (filename, session['user_id']))
            db.commit()
        return redirect(url_for('edit'))
    except Exception as e:
        return f"Произошла ошибка: {e}"
Error=None   

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        try:
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    return render_template('register.html', error=Error)
                cursor = db.cursor()
                query = """ INSERT INTO users (username, email, password) VALUES (?, ?, ?) """
                cursor.execute(query, (username, email, password))
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
            with sqlite3.connect(db_path) as db:
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

if __name__ == "__main__":
    app.run(debug=True, port=5501)
