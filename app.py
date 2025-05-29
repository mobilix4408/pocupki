from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = 'database.db'

# Пользовательский класс
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = cur.fetchone()
        if user:
            return User(user[0], user[1])
        return None

# Инициализация базы данных
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                bought BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        # Добавим тестового пользователя
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                        ("test", "test"))
        except sqlite3.IntegrityError:
            pass
        conn.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cur.fetchone()
            if user:
                user_obj = User(user[0], user[1])
                login_user(user_obj)
                return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        item_name = request.form.get('item')
        if item_name:
            with sqlite3.connect(DATABASE) as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO items (name) VALUES (?)", (item_name,))
                conn.commit()
    elif request.method == 'GET' and 'delete' in request.args:
        item_id = request.args.get('delete')
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM items WHERE id=?", (item_id,))
            conn.commit()
        return redirect(url_for('index'))
    elif request.method == 'GET' and 'toggle' in request.args:
        item_id = request.args.get('toggle')
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE items SET bought=NOT bought WHERE id=?", (item_id,))
            conn.commit()
        return redirect(url_for('index'))

    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM items")
        items = cur.fetchall()

    return render_template('index.html', items=items, user=current_user)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
