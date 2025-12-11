import sqlite3

def init_db():
    conn = sqlite3.connect("pizza.db")
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        phone TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pizza TEXT,
        size TEXT,
        status TEXT DEFAULT 'нове',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        city TEXT,
        table_number INTEGER,
        people INTEGER,
        time TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()


def add_user(user_id, username, name):
    conn = sqlite3.connect("pizza.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username, name) VALUES (?, ?, ?)",
                (user_id, username, name))
    conn.commit()
    conn.close()


def add_order(user_id, pizza, size):
    conn = sqlite3.connect("pizza.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO orders (user_id, pizza, size) VALUES (?, ?, ?)",
                (user_id, pizza, size))
    conn.commit()
    conn.close()


def get_user_orders(user_id):
    conn = sqlite3.connect("pizza.db")
    cur = conn.cursor()
    cur.execute("SELECT id, pizza, size, status FROM orders WHERE user_id = ? ORDER BY id DESC",
                (user_id,))
    orders = cur.fetchall()
    conn.close()
    return orders


def add_reservation(user_id, city, table_number, people, time):
    conn = sqlite3.connect("pizza.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reservations (user_id, city, table_number, people, time)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, city, table_number, people, time))
    conn.commit()
    conn.close()


