import streamlit as st
import pandas as pd
from db import get_conn

st.header("Produção Diária")

conn = get_conn()
cur = conn.cursor()

# -------------------------
# LISTAR PRODUÇÕES
# -------------------------

df_prod = pd.read_sql("SELECT * FROM production ORDER BY id DESC", conn)

if df_prod.empty:
    st.info("Nenhuma produção criada ainda.")
else:
    selected_id = st.selectbox(
        "Selecione a Produção",
        df_prod["id"]
    )

    # Mostrar dados da produção
    prod_info = df_prod[df_prod["id"] == selected_id].iloc[0]

    st.write("Data:", prod_info["prod_date"])
    st.write("Obra:", prod_info["job"])
    st.write("Local:", prod_info["location"])

    # -------------------------
    # LISTAR CARGAS
    # -------------------------
    df_loads = pd.read_sql(
        "SELECT plate, tons FROM production_loads WHERE production_id = ?",
        conn,
        params=(selected_id,)
    )

    if not df_loads.empty:
        st.subheader("Cargas Registradas")
        st.dataframe(df_loads)

        total = df_loads["tons"].sum()
        st.metric("CBUQ Diário (ton)", f"{total:.2f}")

        # Acumulado do mês
        month = prod_info["prod_date"][:7]

        df_month = pd.read_sql(
            """
            SELECT SUM(pl.tons) as total
            FROM production p
            JOIN production_loads pl ON p.id = pl.production_id
            WHERE p.prod_date LIKE ?
            """,
            conn,
            params=(f"{month}%",)
        )

        acumulado = df_month["total"].iloc[0] if df_month["total"].iloc[0] else 0
        st.metric("Acumulado no mês (ton)", f"{acumulado:.2f}")