import streamlit as st
import pandas as pd
from db import get_conn

st.header("Fórmula do Asfalto (%)")

conn = get_conn()

# --- Add new item ---
with st.expander("Cadastrar novo material"):
    name = st.text_input("Nome do material (ex: Brita 1)")
    unit = st.selectbox("Unidade", ["ton", "m3", "L", "saco"])
    low = st.number_input("Estoque mínimo", min_value=0.0)

    if st.button("Salvar material"):
        conn.execute(
            "INSERT OR IGNORE INTO items(name, unit, low_stock) VALUES(?,?,?)",
            (name, unit, low),
        )
        conn.commit()
        st.success("Material salvo!")

# --- Show items ---
df = pd.read_sql("SELECT * FROM items", conn)

if not df.empty:
    st.subheader("Definir percentual da fórmula")

    for _, row in df.iterrows():
        percent = st.number_input(
            f"{row['name']} (%)",
            min_value=0.0,
            max_value=100.0,
            key=row["id"],
        )

        conn.execute(
            "INSERT INTO asphalt_formula(item_id, percent) VALUES(?,?) "
            "ON CONFLICT(item_id) DO UPDATE SET percent=excluded.percent;",
            (row["id"], percent),
        )

    conn.commit()

conn.close()