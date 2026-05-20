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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fleet_equipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        equipment_type TEXT NOT NULL,
        plate TEXT,
        current_km REAL DEFAULT 0,
        current_hours REAL DEFAULT 0,
        notes TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fleet_maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        maintenance_date TEXT NOT NULL,
        service_type TEXT NOT NULL,
        description TEXT,
        cost REAL DEFAULT 0,
        current_km REAL DEFAULT 0,
        current_hours REAL DEFAULT 0,
        next_due_date TEXT,
        next_due_km REAL,
        next_due_hours REAL,
        FOREIGN KEY(equipment_id) REFERENCES fleet_equipments(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fleet_stock_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        unit TEXT NOT NULL,
        min_stock REAL DEFAULT 0,
        current_stock REAL DEFAULT 0,
        unit_cost REAL DEFAULT 0
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fleet_stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mov_date TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        movement_type TEXT NOT NULL,
        qty REAL NOT NULL,
        equipment_id INTEGER,
        maintenance_id INTEGER,
        notes TEXT,
        FOREIGN KEY(item_id) REFERENCES fleet_stock_items(id),
        FOREIGN KEY(equipment_id) REFERENCES fleet_equipments(id),
        FOREIGN KEY(maintenance_id) REFERENCES fleet_maintenance(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        client TEXT,
        location TEXT,
        total_asphalt_tons REAL DEFAULT 0,
        status TEXT DEFAULT 'Planejado'
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_material_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        planned_qty REAL NOT NULL,
        unit_cost REAL DEFAULT 0,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_daily_production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        prod_date TEXT NOT NULL,
        produced_tons REAL DEFAULT 0,
        produced_percent REAL DEFAULT 0,
        notes TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_extra_outputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        output_date TEXT NOT NULL,
        qty REAL NOT NULL,
        notes TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    );
    """)

        # Add missing columns safely
    try:
        cur.execute("ALTER TABLE items ADD COLUMN unit_cost REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE stock_movements ADD COLUMN project_id INTEGER")
    except sqlite3.OperationalError:
        pass

    try:
        cur.execute("ALTER TABLE financial_movements ADD COLUMN project_id INTEGER")
    except sqlite3.OperationalError:
        pass

    # Purchase history for materials
    cur.execute("""
    CREATE TABLE IF NOT EXISTS material_purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_date TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        qty REAL NOT NULL,
        unit TEXT,
        total_value REAL NOT NULL,
        unit_cost REAL NOT NULL,
        project_id INTEGER,
        supplier TEXT,
        notes TEXT,
        FOREIGN KEY(item_id) REFERENCES items(id),
        FOREIGN KEY(project_id) REFERENCES projects(id)
    );
    """)
    conn.commit()
    conn.close()