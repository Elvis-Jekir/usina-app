import streamlit as st
import pandas as pd
from db import get_conn

st.header("Controle de Estoque")

conn = get_conn()

# -------------------------
# SALDO ATUAL
# -------------------------

st.subheader("Saldo Atual dos Materiais")

df_saldo = pd.read_sql("""
SELECT 
    i.id,
    i.name,
    i.unit,
    i.low_stock,
    i.unit_cost,
    COALESCE(SUM(sm.qty), 0) AS saldo
FROM items i
LEFT JOIN stock_movements sm 
    ON sm.item_id = i.id
GROUP BY i.id
ORDER BY i.name
""", conn)

if not df_saldo.empty:

    def get_status(row):
        if row["saldo"] <= row["low_stock"]:
            return "⚠ REPOSIÇÃO NECESSÁRIA"
        else:
            return "✅ ESTOQUE OK"

    df_saldo["status"] = df_saldo.apply(get_status, axis=1)

    df_show = df_saldo.rename(columns={
        "name": "Material",
        "unit": "Unidade",
        "saldo": "Saldo Atual",
        "low_stock": "Estoque Mínimo",
        "unit_cost": "Custo Unitário"
    })

    st.dataframe(
        df_show[
            [
                "Material",
                "Unidade",
                "Saldo Atual",
                "Estoque Mínimo",
                "Custo Unitário",
                "status"
            ]
        ],
        use_container_width=True
    )

else:
    st.info("Nenhum material cadastrado.")
