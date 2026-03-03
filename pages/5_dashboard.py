import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_conn

st.header("Dashboard Financeiro")

conn = get_conn()

df = pd.read_sql("SELECT * FROM financial_movements", conn)

if df.empty:
    st.info("Nenhum dado financeiro ainda.")
else:

    df["mov_date"] = pd.to_datetime(df["mov_date"])
    df["month"] = df["mov_date"].dt.to_period("M").astype(str)

    entradas = df[df["type"] == "Entrada"]["amount"].sum()
    saidas = df[df["type"] == "Saída"]["amount"].sum()
    saldo = entradas - saidas

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Entradas", f"R$ {entradas:,.2f}")
    col2.metric("Total Saídas", f"R$ {saidas:,.2f}")
    col3.metric("Saldo", f"R$ {saldo:,.2f}")

    # Gráfico mensal
    df_group = df.groupby(["month", "type"])["amount"].sum().reset_index()

    fig = px.bar(
        df_group,
        x="month",
        y="amount",
        color="type",
        barmode="group",
        title="Entradas vs Saídas Mensais"
    )

    st.plotly_chart(fig, use_container_width=True)

conn.close()