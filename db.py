from pathlib import Path
import sqlite3

DB_PATH = Path("data/usina.sqlite")

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        unit TEXT NOT NULL,
        low_stock REAL DEFAULT 0
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS asphalt_formula (
        item_id INTEGER PRIMARY KEY,
        percent REAL NOT NULL,
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prod_date TEXT NOT NULL,
        job TEXT NOT NULL,
        location TEXT,
        notes TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS production_loads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        production_id INTEGER NOT NULL,
        plate TEXT NOT NULL,
        tons REAL NOT NULL,
        FOREIGN KEY(production_id) REFERENCES production(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mov_date TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        qty REAL NOT NULL,
        ref_type TEXT NOT NULL,
        ref_id INTEGER,
        notes TEXT,
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS financial_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mov_date TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL
    );
    """)

    conn.commit()
    conn.close()