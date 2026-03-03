import streamlit as st
import pandas as pd
from db import get_conn

st.header("Controle de Estoque")

conn = get_conn()
cur = conn.cursor()

# -------------------------
# SALDO ATUAL
# -------------------------

st.subheader("Saldo Atual")

df_saldo = pd.read_sql("""
SELECT i.name, i.unit, 
       COALESCE(SUM(m.qty),0) as saldo
FROM items i
LEFT JOIN stock_movements m ON i.id = m.item_id
GROUP BY i.id
ORDER BY i.name
""", conn)

st.dataframe(df_saldo)

# -------------------------
# MOVIMENTAÇÃO
# -------------------------

st.subheader("Nova Movimentação")

items = pd.read_sql("SELECT id, name FROM items", conn)

if not items.empty:
    item_dict = dict(zip(items["name"], items["id"]))

    selected_item = st.selectbox("Material", items["name"])

    tipo = st.selectbox("Tipo", ["Entrada", "Saída"])

    quantidade = st.number_input("Quantidade", min_value=0.0)

    if st.button("Registrar Movimentação"):
        item_id = item_dict[selected_item]

        if tipo == "Saída":
            quantidade = -quantidade

        cur.execute("""
            INSERT INTO stock_movements 
            (mov_date, item_id, qty, ref_type, ref_id, notes)
            VALUES (date('now'), ?, ?, 'manual', NULL, 'Movimentação Manual')
        """, (item_id, quantidade))

        conn.commit()
        st.success("Movimentação registrada!")
        st.rerun()

conn.close()