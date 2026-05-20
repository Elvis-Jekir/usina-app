import streamlit as st
import pandas as pd
from db import get_conn

st.header("Produção Diária por Projeto")

conn = get_conn()
cur = conn.cursor()

projects = pd.read_sql("""
SELECT id, name, client, location, total_asphalt_tons, status
FROM projects
ORDER BY name
""", conn)

if projects.empty:
    st.warning("Cadastre um projeto primeiro.")
    conn.close()
    st.stop()

projects["label"] = projects["name"] + " | " + projects["total_asphalt_tons"].astype(str) + " ton"
project_map = dict(zip(projects["label"], projects["id"]))

selected_project_label = st.selectbox("Projeto", projects["label"])
project_id = project_map[selected_project_label]

project = projects[projects["id"] == project_id].iloc[0]
total_project_tons = float(project["total_asphalt_tons"])

st.write(f"**Cliente:** {project['client']}")
st.write(f"**Local:** {project['location']}")
st.write(f"**Total previsto:** {total_project_tons:.2f} ton")
st.write(f"**Status:** {project['status']}")

st.divider()

# Produção já lançada
produced_df = pd.read_sql("""
SELECT COALESCE(SUM(produced_tons), 0) AS produced
FROM project_daily_production
WHERE project_id = ?
""", conn, params=(project_id,))

produced_so_far = float(produced_df["produced"].iloc[0])
remaining = total_project_tons - produced_so_far
progress = (produced_so_far / total_project_tons * 100) if total_project_tons > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Produzido até agora", f"{produced_so_far:.2f} ton")
c2.metric("Falta produzir", f"{remaining:.2f} ton")
c3.metric("% concluído", f"{progress:.2f}%")

st.divider()

st.subheader("Registrar produção do dia")

prod_date = st.date_input("Data")
produced_today = st.number_input("Quantidade produzida hoje (ton)", min_value=0.0, value=0.0)
notes = st.text_area("Observações")

# Ficha técnica do projeto
plan = pd.read_sql("""
SELECT
    pmp.item_id,
    i.name AS material,
    i.unit,
    pmp.planned_qty
FROM project_material_plan pmp
JOIN items i ON i.id = pmp.item_id
WHERE pmp.project_id = ?
""", conn, params=(project_id,))

if plan.empty:
    st.warning("Este projeto ainda não tem materiais na ficha técnica.")
    conn.close()
    st.stop()

if total_project_tons > 0 and produced_today > 0:
    production_ratio = produced_today / total_project_tons

    plan["consumo_hoje"] = plan["planned_qty"] * production_ratio

    st.subheader("Consumo calculado para hoje")
    st.dataframe(
        plan[["material", "unit", "planned_qty", "consumo_hoje"]],
        use_container_width=True
    )

if st.button("Salvar produção e baixar estoque"):

    if produced_today <= 0:
        st.error("Informe uma quantidade produzida maior que zero.")
        conn.close()
        st.stop()

    production_ratio = produced_today / total_project_tons

    cur.execute("""
        INSERT INTO project_daily_production
        (project_id, prod_date, produced_tons, produced_percent, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        project_id,
        prod_date.isoformat(),
        produced_today,
        production_ratio * 100,
        notes
    ))

    production_id = cur.lastrowid

    for _, row in plan.iterrows():
        consumed_qty = float(row["planned_qty"]) * production_ratio

        cur.execute("""
            INSERT INTO stock_movements
            (mov_date, item_id, qty, ref_type, ref_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            prod_date.isoformat(),
            int(row["item_id"]),
            -consumed_qty,
            "project_production",
            production_id,
            f"Baixa automática da produção do projeto {project['name']}"
        ))

    # Se estava planejado, muda para Em produção
    if project["status"] == "Planejado":
        cur.execute("""
            UPDATE projects
            SET status = 'Em produção'
            WHERE id = ?
        """, (project_id,))

    conn.commit()
    st.success("Produção registrada e estoque atualizado!")
    st.rerun()

st.divider()

st.subheader("Histórico de produção deste projeto")

history = pd.read_sql("""
SELECT
    prod_date AS Data,
    produced_tons AS Toneladas,
    produced_percent AS Percentual,
    notes AS Observacoes
FROM project_daily_production
WHERE project_id = ?
ORDER BY prod_date DESC
""", conn, params=(project_id,))

st.dataframe(history, use_container_width=True)

conn.close()