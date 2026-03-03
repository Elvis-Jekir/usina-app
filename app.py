import streamlit as st
from db import init_db, get_conn
import sqlite3

st.set_page_config(page_title="Sistema Usina", layout="wide")

init_db()

st.title("Sistema da Usina de Asfalto")

conn = get_conn()
cur = conn.cursor()

if st.button("Inicializar Sistema com Dados Demo"):
    
    # ---- MATERIAIS ----
    materiais = [
        ("Brita 1", "ton", 50),
        ("Brita 0", "ton", 50),
        ("Pó de Brita", "ton", 50),
        ("Areia Grossa", "ton", 50),
        ("CAP (Betuminoso)", "ton", 20),
        ("Diesel", "L", 500),
    ]

    for nome, unidade, estoque_inicial in materiais:
        cur.execute(
            "INSERT OR IGNORE INTO items (name, unit, low_stock) VALUES (?,?,?)",
            (nome, unidade, 10)
        )
        conn.commit()

        # pegar id do material
        cur.execute("SELECT id FROM items WHERE name=?", (nome,))
        item_id = cur.fetchone()[0]

        # inserir estoque inicial
        cur.execute(
            "INSERT INTO stock_movements (mov_date, item_id, qty, ref_type, ref_id, notes) VALUES (?,?,?,?,?,?)",
            ("2026-01-01", item_id, estoque_inicial, "init", None, "Estoque Inicial")
        )

    # ---- FORMULA ----
    formula = {
        "Brita 1": 30,
        "Brita 0": 25,
        "Pó de Brita": 20,
        "Areia Grossa": 15,
        "CAP (Betuminoso)": 10,
    }

    for nome, percent in formula.items():
        cur.execute("SELECT id FROM items WHERE name=?", (nome,))
        item_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO asphalt_formula (item_id, percent) VALUES (?,?) "
            "ON CONFLICT(item_id) DO UPDATE SET percent=excluded.percent;",
            (item_id, percent)
        )

    # ---- PRODUÇÃO EXEMPLO ----
    cur.execute(
        "INSERT INTO production (prod_date, job, location) VALUES (?,?,?)",
        ("2026-01-22", "Chrome Construction Inc", "Mauraunau Village")
    )
    conn.commit()
    prod_id = cur.lastrowid

    cargas = [
        ("NPC-1", 35),
        ("NPC-2", 35),
        ("GAH-4186", 30),
        ("GAK-6603", 30),
        ("GAG-5359", 27),
        ("GAK-9949", 30),
        ("GAH-4185", 30),
    ]

    for placa, ton in cargas:
        cur.execute(
            "INSERT INTO production_loads (production_id, plate, tons) VALUES (?,?,?)",
            (prod_id, placa, ton)
        )

    conn.commit()

        # ---- FINANCEIRO DEMO ----
    finance_demo = [
        ("2026-01-05", "Entrada", "Venda Asfalto", "Obra Chrome", 80000),
        ("2026-01-06", "Saída", "Combustível", "Diesel produção", 15000),
        ("2026-01-07", "Saída", "Funcionários", "Folha pagamento", 25000),
        ("2026-01-08", "Saída", "Luz", "Conta mensal", 5000),
        ("2026-02-01", "Entrada", "Venda Asfalto", "Obra Mauraunau", 95000),
        ("2026-02-03", "Saída", "Compra Brita", "Fornecedor X", 30000),
    ]

    for data, tipo, categoria, desc, valor in finance_demo:
        cur.execute("""
            INSERT INTO financial_movements
            (mov_date, type, category, description, amount)
            VALUES (?, ?, ?, ?, ?)
        """, (data, tipo, categoria, desc, valor))

    conn.commit()



    st.success("Sistema inicializado com dados reais de exemplo!")

conn.close()