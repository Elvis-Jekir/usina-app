import streamlit as st
import pandas as pd
from db import get_conn

st.header("Saída Avulsa por Projeto")

conn = get_conn()
cur = conn.cursor()

projects = pd.read_sql("""
SELECT id, name, client, location
FROM projects
ORDER BY name
""", conn)

items = pd.read_sql("""
SELECT id, name, unit
FROM items
ORDER BY name
""", conn)

if projects.empty:
    st.warning("Cadastre um projeto primeiro.")
    conn.close()
    st.stop()

if items.empty:
    st.warning("Cadastre materiais primeiro.")
    conn.close()
    st.stop()

projects["label"] = projects["name"] + " | " + projects["location"].fillna("")
project_map = dict(zip(projects["label"], projects["id"]))

items["label"] = items["name"] + " (" + items["unit"] + ")"
item_map = dict(zip(items["label"], items["id"]))

st.subheader("Registrar saída avulsa")

selected_project = st.selectbox("Projeto", projects["label"])
project_id = project_map[selected_project]

selected_item = st.selectbox("Material", items["label"])
item_id = item_map[selected_item]

output_date = st.date_input("Data da saída")
qty = st.number_input("Quantidade", min_value=0.0, value=0.0)
reason = st.text_area("Motivo / descrição")

if st.button("Salvar saída avulsa"):

    if qty <= 0:
        st.error("Informe uma quantidade maior que zero.")
        conn.close()
        st.stop()

    cur.execute("""
        INSERT INTO project_extra_outputs
        (project_id, item_id, output_date, qty, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        project_id,
        item_id,
        output_date.isoformat(),
        qty,
        reason
    ))

    extra_output_id = cur.lastrowid

    cur.execute("""
        INSERT INTO stock_movements
        (mov_date, item_id, qty, ref_type, ref_id, project_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        output_date.isoformat(),
        item_id,
        -qty,
        "extra_output",
        extra_output_id,
        project_id,
        f"Saída avulsa vinculada ao projeto {selected_project}"
    ))

    conn.commit()
    st.success("Saída avulsa registrada e estoque atualizado!")
    st.rerun()

st.divider()

st.subheader("Saídas avulsas registradas")

df = pd.read_sql("""
SELECT
    peo.output_date AS Data,
    p.name AS Projeto,
    i.name AS Material,
    peo.qty AS Quantidade,
    peo.notes AS Motivo
FROM project_extra_outputs peo
JOIN projects p ON p.id = peo.project_id
JOIN items i ON i.id = peo.item_id
ORDER BY peo.id DESC
""", conn)

if df.empty:
    st.info("Nenhuma saída avulsa registrada.")
else:
    st.dataframe(df, use_container_width=True)

conn.close()