import streamlit as st
import pandas as pd
from db import get_conn

st.header("Cadastro da Frota")

conn = get_conn()
cur = conn.cursor()

# -------------------------
# CADASTRO
# -------------------------

st.subheader("Novo equipamento")

name = st.text_input("Nome", placeholder="Ex: Caminhão 1")

equipment_type = st.selectbox(
    "Tipo",
    [
        "Caminhão basculante",
        "Outro caminhão",
        "Usina de asfalto",
        "Usina de concreto",
        "Rolo compactador",
        "Acabadora",
        "Pá carregadeira",
        "Bobcat",
        "Retroescavadeira"
    ]
)

plate = st.text_input("Placa")

current_km = st.number_input("KM atual", min_value=0.0)


notes = st.text_area("Observações")

if st.button("Salvar equipamento"):

    cur.execute("""
        INSERT INTO fleet_equipments
        (name, equipment_type, plate, current_km, current_hours, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        equipment_type,
        plate,
        current_km,
        current_hours,
        notes
    ))

    conn.commit()

    st.success("Equipamento cadastrado!")

    st.rerun()

# -------------------------
# LISTA
# -------------------------

st.divider()

st.subheader("Equipamentos cadastrados")

df = pd.read_sql("""
SELECT
    id,
    name,
    equipment_type,
    plate,
    current_km,
    current_hours
FROM fleet_equipments
ORDER BY id DESC
""", conn)

if df.empty:
    st.info("Nenhum equipamento cadastrado ainda.")
else:
    st.dataframe(df, use_container_width=True)

conn.close()