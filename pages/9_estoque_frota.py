import streamlit as st
import pandas as pd
from db import get_conn

st.header("Estoque da Frota")

conn = get_conn()
cur = conn.cursor()

st.subheader("Cadastrar item de manutenção")

name = st.text_input("Item", placeholder="Ex: Pneu, Óleo 15W40, Filtro")
unit = st.selectbox("Unidade", ["unidade", "litro", "galão", "peça"])
min_stock = st.number_input("Estoque mínimo", min_value=0.0)
current_stock = st.number_input("Quantidade inicial", min_value=0.0)
unit_cost = st.number_input("Custo unitário", min_value=0.0)
launch_finance_purchase = st.checkbox("Lançar compra inicial no financeiro?")

if st.button("Salvar item"):
    cur.execute("""
        INSERT OR IGNORE INTO fleet_stock_items
        (name, unit, min_stock, current_stock, unit_cost)
        VALUES (?, ?, ?, ?, ?)
    """, (name, unit, min_stock, current_stock, unit_cost))
    if launch_finance_purchase and current_stock > 0 and unit_cost > 0:
        total_cost = current_stock * unit_cost

        cur.execute("""
            INSERT INTO financial_movements
            (mov_date, type, category, description, amount)
            VALUES (date('now'), ?, ?, ?, ?)
        """, (
            "Saída",
            "Compra Estoque Frota",
            f"Compra inicial de {name}",
            total_cost
        ))

    conn.commit()
    st.success("Item salvo!")
    st.rerun()

st.divider()

st.subheader("Saldo de itens da frota")

df = pd.read_sql("""
SELECT
    name AS Item,
    unit AS Unidade,
    current_stock AS Estoque,
    min_stock AS Minimo,
    unit_cost AS Custo_Unitario,
    CASE
        WHEN current_stock <= min_stock THEN 'COMPRAR'
        ELSE 'OK'
    END AS Status
FROM fleet_stock_items
ORDER BY name
""", conn)

if df.empty:
    st.info("Nenhum item cadastrado ainda.")
else:
    st.dataframe(df, use_container_width=True)

