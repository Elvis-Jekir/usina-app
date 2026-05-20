import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_conn

st.header("Dashboard Geral da Usina")

conn = get_conn()

# -------------------------
# FINANCEIRO
# -------------------------

df_fin = pd.read_sql("""
SELECT mov_date, type, category, amount
FROM financial_movements
""", conn)

if not df_fin.empty:
    df_fin["mov_date"] = pd.to_datetime(df_fin["mov_date"])
    df_fin["month"] = df_fin["mov_date"].dt.strftime("%Y-%m")

    mes_atual = pd.Timestamp.today().strftime("%Y-%m")
    df_mes = df_fin[df_fin["month"] == mes_atual]

    entradas_mes = df_mes[df_mes["type"] == "Entrada"]["amount"].sum()
    saidas_mes = df_mes[df_mes["type"] == "Saída"]["amount"].sum()
    saldo_mes = entradas_mes - saidas_mes
else:
    entradas_mes = 0
    saidas_mes = 0
    saldo_mes = 0

# -------------------------
# ESTOQUE CRÍTICO
# -------------------------

df_stock = pd.read_sql("""
SELECT 
    i.name AS Material,
    i.unit AS Unidade,
    i.low_stock AS Minimo,
    COALESCE(SUM(sm.qty), 0) AS Saldo
FROM items i
LEFT JOIN stock_movements sm ON sm.item_id = i.id
GROUP BY i.id
ORDER BY i.name
""", conn)

estoque_critico = df_stock[df_stock["Saldo"] <= df_stock["Minimo"]] if not df_stock.empty else pd.DataFrame()

# -------------------------
# PRODUÇÃO POR PROJETO
# -------------------------

df_prod = pd.read_sql("""
SELECT 
    p.name AS Projeto,
    p.total_asphalt_tons AS Total_Previsto,
    COALESCE(SUM(pdp.produced_tons), 0) AS Produzido
FROM projects p
LEFT JOIN project_daily_production pdp ON pdp.project_id = p.id
GROUP BY p.id
ORDER BY p.name
""", conn)

if not df_prod.empty:
    df_prod["Falta"] = df_prod["Total_Previsto"] - df_prod["Produzido"]
    df_prod["Conclusao_%"] = df_prod.apply(
        lambda row: (row["Produzido"] / row["Total_Previsto"] * 100) if row["Total_Previsto"] > 0 else 0,
        axis=1
    )

# -------------------------
# CARDS
# -------------------------

c1, c2 = st.columns(2)
c1.metric("Entradas do mês", f"R$ {entradas_mes:,.2f}")
c2.metric("Saídas do mês", f"R$ {saidas_mes:,.2f}")

c3, c4 = st.columns(2)
c3.metric("Saldo do mês", f"R$ {saldo_mes:,.2f}")
c4.metric("Itens em alerta", len(estoque_critico))

st.divider()

# -------------------------
# GRÁFICO FINANCEIRO
# -------------------------

st.subheader("Financeiro mensal")

if not df_fin.empty:
    df_group = df_fin.groupby(["month", "type"], as_index=False)["amount"].sum()

    fig = px.bar(
        df_group,
        x="month",
        y="amount",
        color="type",
        barmode="group",
        title="Entradas vs Saídas por mês"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhuma movimentação financeira registrada.")

st.divider()

# -------------------------
# PROJETOS
# -------------------------

st.subheader("Progresso dos projetos")

if df_prod.empty:
    st.info("Nenhum projeto cadastrado.")
else:
    st.dataframe(df_prod, use_container_width=True)

    df_prod["Conclusao_%"] = df_prod["Conclusao_%"].round(2)

fig_proj = px.bar(
    df_prod,
    x="Projeto",
    y="Conclusao_%",
    text="Conclusao_%",
    title="Percentual concluído por projeto"
)

fig_proj.update_yaxes(range=[0, 100], title="Conclusão (%)")
fig_proj.update_traces(texttemplate="%{text:.2f}%", textposition="outside")

st.plotly_chart(fig_proj, use_container_width=True)

st.divider()

# -------------------------
# ESTOQUE CRÍTICO
# -------------------------

st.subheader("Materiais com necessidade de reposição")

if estoque_critico.empty:
    st.success("Nenhum material abaixo do estoque mínimo.")
else:
    st.warning("Existem materiais que precisam de reposição.")
    st.dataframe(estoque_critico, use_container_width=True)

conn.close()