from flask import Flask, request, render_template, session, redirect, url_for
from flask_session import Session
import sqlite3
import bcrypt
import html
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FlaskKey']
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

DATABASE = 'database.db'
TABLE = 'database'

def create_users_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(32) NOT NULL UNIQUE,
                password VARCHAR(60) NOT NULL)
                ''')
    
    # Create the Items table
    c.execute('''CREATE TABLE IF NOT EXISTS Items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(64) NOT NULL,
                description VARCHAR(256) NOT NULL)''')

    conn.commit()
    conn.close()

create_users_table()

def insert_books():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    books = [
        ("Il Signore degli Anelli", "Una grande saga fantasy che narra le avventure di Frodo e del suo viaggio per distruggere l'Anello del Potere."),
        ("Guide To Competitive Programming", "Un libro completo che copre tutti gli aspetti della programmazione competitiva."),
        ("9 Algoritmi che hanno cambiato il mondo", "Una raccolta di nove algoritmi rivoluzionari che hanno avuto un impatto significativo nel campo della scienza e della tecnologia."),
        ("1984", "Un romanzo distopico scritto da George Orwell che dipinge una società totalitaria e oppressiva."),
        ("Algebra Baldor", "Un libro di algebra che fornisce una guida completa ai concetti e alle tecniche di base dell'algebra.")
    ]

    for book in books:
        name, description = book
        c.execute("SELECT * FROM Items WHERE name = ?", (name,))
        existing_book = c.fetchone()

        if existing_book:
            continue

        c.execute("INSERT INTO Items (name, description) VALUES (?, ?)", book)

    conn.commit()
    conn.close()

insert_books()

def html_escaping(string):
    try:
        string = html.escape(string)
    except:
        string = ""
    return string

def check_len(string, int =0):
    if len(str(string)) > int:
        return True
    else:
        return False

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM Items")
    items = c.fetchall()
    conn.close()

    return render_template('index.html', items=items)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:    
            if check_len(username,32) or len(str(username)) < 4:
                return render_template('register.html', error_message="L'Username dev'essere tra 4 e 32 Caratteri!")
            if check_len(password,64) or len(str(password)) < 8:
                return render_template('register.html', error_message="La Password dev'essere tra 8 e 64 Caratteri!")
        except:
            return redirect(url_for('register.html'))
        
        username = html_escaping(username)
        password = html_escaping(password)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        query = "SELECT COUNT(*) FROM Users WHERE username = ?"
        c.execute(query, (username,))
        result = c.fetchone()

        if result[0] > 0:
            error_message = "Username Già Esistente!  ☹️"
            return render_template('register.html', error_message=error_message)

        salt = bcrypt.gensalt()
        password_bytes = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        query = "INSERT INTO Users (username, password) VALUES (?, ?)"
        c.execute(query, (username, hashed_password))

        conn.commit()
        conn.close()


        session['username'] = username

        return redirect(url_for('index'))
    else:
        return render_template('register.html', error_message=None)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        try:
            if check_len(username,32) or len(str(username)) < 4:
                return render_template('login.html', error_message="L'Username dev'essere tra 4 e 32 Caratteri!")
            if check_len(password,64) or len(str(password)) < 8:
                return render_template('login.html', error_message="La Password dev'essere tra 8 e 64 Caratteri!")
        except:
            return redirect(url_for('login.html'))
        
        username = html_escaping(username)
        password = html_escaping(password)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            queryhash = "SELECT password FROM Users where username = ?"
            c.execute(queryhash,(username,))
            password_hashed = c.fetchone()
            password_hashed = password_hashed[0]
            password_bytes = password.encode('utf-8')
            result = bcrypt.checkpw(password_bytes, password_hashed)
        except:
            return render_template('login.html', error_message='Utente non trovato!')
        if result:
            query = "SELECT * FROM Users WHERE username = ? AND password = ?"
            c.execute(query, (username, password_hashed))
            user = c.fetchone()
            conn.close()
        else:
            return render_template('login.html', error_message='Username o Password errati! ')
        
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error_message='Username o Password errati! ')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    item_id = request.form['item_id']
    try:
        if check_len(item_id,2) != True:
            item_id = str(item_id[:2:])
    except:
        return redirect(url_for('index'))
    
    try:
        if len(item_id) < 0 or int(item_id) < 0:
            return redirect(url_for('index'))
    except:
        return redirect(url_for('index'))
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    query = f"SELECT id FROM Items"
    c.execute(query)
    items = c.fetchall()
    items = [str(item[0]) for item in items]
    if str(item_id) not in items:
        return redirect(url_for('index'))
        
    query = f"SELECT * FROM Items WHERE id = {item_id}"
    c.execute(query)
    item = c.fetchone()
    conn.close()

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append(item)
    setsession = set(session['cart'])
    session['cart'] = list(setsession)

    return redirect(url_for('index'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    item_id = request.form['item_id']
    if 'cart' in session:
        newitems = []
        for item in session['cart']:
            if int(item[0]) != int(item_id):
                newitems.append(item)
                print(f"{item[0]} {item_id}")

        session['cart'] = newitems

    return redirect(url_for('index'))


@app.route('/search')
def search():
    params_get = request.args.get('query').strip()
    """ INELUTTABILE """
    try:
        vuln = request.args.get('vuln').strip()
        vuln = int(vuln)
    except:
        vuln =  0

    if params_get == "":
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM Items")
        items = c.fetchall()
        conn.close()
        return render_template('index.html', query=params_get, items = items)
    if check_len(params_get, 32):
        params_get = params_get[:29:] + "..."

    if not params_get:
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if vuln == 1:
        print("Flag Vulnerabile")
        """ CODICE VULNERABILE AD SQL INJECTION """ 
        query = f"SELECT * FROM Items WHERE name LIKE '%{params_get}%'"
        print(query)
        c.execute(query)
        items = c.fetchall()
    elif vuln == 0:
        """ FIX SQL INJECTION """
        params_get = html_escaping(params_get)

        query = "SELECT * FROM Items WHERE name LIKE ?"
        params = ("%{params}%".format(params=params_get),)
        c.execute(query,params)
        items = c.fetchall()
        """ FINE FIX """
    else:
        return render_template('index.html')
    
    conn.close()
    return render_template('index.html', query=params_get, items=items)


if __name__ == '__main__':
    print("Listening on Port 5000")
    app.run(host='0.0.0.0', port=5000)
