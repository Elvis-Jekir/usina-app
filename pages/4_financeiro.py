import streamlit as st
import pandas as pd
from db import get_conn

st.header("Fluxo de Caixa")

conn = get_conn()
cur = conn.cursor()

# -------------------------
# REGISTRAR MOVIMENTAÇÃO
# -------------------------

st.subheader("Nova Movimentação")

tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
categoria = st.text_input("Categoria")
descricao = st.text_input("Descrição")
valor = st.number_input("Valor", min_value=0.0)

if st.button("Registrar"):
    cur.execute("""
        INSERT INTO financial_movements 
        (mov_date, type, category, description, amount)
        VALUES (date('now'), ?, ?, ?, ?)
    """, (tipo, categoria, descricao, valor))
    conn.commit()
    st.success("Movimentação registrada!")
    st.rerun()

# -------------------------
# LISTAR MOVIMENTAÇÕES
# -------------------------

st.subheader("Histórico")

df = pd.read_sql("""
SELECT mov_date, type, category, description, amount
FROM financial_movements
ORDER BY mov_date DESC
""", conn)

st.dataframe(df)

conn.close()