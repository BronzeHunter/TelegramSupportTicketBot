# db.py
import sqlite3

# Функция для создания базы данных тикетов
def create_database():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        client_name TEXT,
        organization TEXT,
        description TEXT,
        status TEXT DEFAULT 'Открыт ⌛',
        comments TEXT DEFAULT '',
        feedback TEXT DEFAULT ''
    )
    ''')
    conn.commit()
    conn.close()
