from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'yourmom'  # Установите секретный ключ для сессий

# Главная страница
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


    
    
    


# Страница регистрации
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            with sqlite3.connect('./datab/database.db') as db:
                cursor = db.cursor()
                query = """ INSERT INTO users (username, email, password) VALUES (?, ?, ?) """
                cursor.execute(query, (username, email, password))
                db.commit()

                # Сохраняем user_id в сессии для авторизации
                session['user_id'] = cursor.lastrowid

            return redirect(url_for('mainpage'))

        except sqlite3.IntegrityError:
            return "Ошибка: пользователь с таким email уже существует!"

    return render_template("testpage.html")

# Выход из аккаунта
@app.route("/logout")
def logout():
    session.pop('user_id', None)  # Удаляем user_id из сессии
    return redirect(url_for('mainpage'))

if __name__ == "__main__":
    app.run(debug=True, port=5501)
