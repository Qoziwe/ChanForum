from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os



app = Flask(__name__)
app.secret_key = 'yourmom'  # your mom





# main page
@app.route("/")
def mainpage():
    # Проверяем, авторизован ли пользователь
    if 'user_id' in session:
        with sqlite3.connect('./datab/database.db') as db:
            cursor = db.cursor()
            # Получаем имя пользователя из базы данных по user_id
            cursor.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()
            if user:
                username = user[0]
                return render_template("mainpage.html", username=username)  # Передаем username в шаблон

    # Если пользователь не авторизован, отображаем кнопку регистрации
    return render_template("mainpage.html", username=None)


# profile page
@app.route('/profile')
def profile():
    if 'user_id' in session:
        with sqlite3.connect('./datab/database.db') as db:
            cursor = db.cursor()
            # Получаем username и email из базы данных по user_id за один запрос
            cursor.execute("SELECT username, email FROM users WHERE id = ?", (session['user_id'],))
            user = cursor.fetchone()

            if user:
                username = user[0]  # Извлекаем username
                email = user[1]  # Извлекаем email
                return render_template("profile.html", username=username, email=email)  # Передаем и username, и email
            else:
                return redirect(url_for('login'))  # Если user не найден, перенаправляем на страницу логина
    else:
        return redirect(url_for('login'))  # Если нет user_id в сессии, перенаправляем на страницу логина



@app.route("/edit")
def edit_profile():
    if 'user_id' in session:
        with sqlite3.connect('./datab/database.db') as db:
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
        with sqlite3.connect('./datab/database.db') as db:
            cursor = db.cursor()
            cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, session['user_id']))
            db.commit()  # Не забудьте зафиксировать изменения
            
            # Обновляем email
            if email and email.strip():
                cursor.execute("UPDATE users SET email = ? WHERE id = ?", (email.strip(), session['user_id']))
            
            # Обновляем пароль
            if password and password.strip():
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (password.strip(), session['user_id']))
            
            # Сохраняем фото профиля
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
            with sqlite3.connect('./datab/database.db') as db:

                cursor = db.cursor()
                # Проверяем, существует ли пользователь с таким email
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return render_template('register.html', error=Error)

                cursor = db.cursor()
                query = """ INSERT INTO users (username, email, password) VALUES (?, ?, ?) """
                cursor.execute(query, (username, email, password))
                db.commit()

                # Сохраняем user_id в сессии для авторизации
                session['user_id'] = cursor.lastrowid

            return redirect(url_for('mainpage'))

        except sqlite3.IntegrityError:
            return "Ошибка: пользователь с таким email уже существует!"

    return render_template("register.html")


# login page
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            with sqlite3.connect('./datab/database.db') as db:
                cursor = db.cursor()
                # Проверяем, существует ли пользователь с таким email и паролем
                cursor.execute("SELECT id, username FROM users WHERE email = ? AND password = ?", (email, password))
                user = cursor.fetchone()

                if user:
                    session['user_id'] = user[0]  # Устанавливаем user_id в сессии
                    username = user[1]
                    return redirect(url_for('mainpage', username=username))  # Переход на главную страницу
                else:
                   return render_template("login.html", error=Error) 

        except sqlite3.IntegrityError:
            return "Ошибка: пользователь с таким email уже существует!"
    
    return render_template("login.html")

#not working yet







# Выход из аккаунта
@app.route("/logout")
def logout():
    session.pop('user_id', None)  # Удаляем user_id из сессии
    return redirect(url_for('mainpage'))

if __name__ == "__main__":
    app.run(debug=True, port=5501)
