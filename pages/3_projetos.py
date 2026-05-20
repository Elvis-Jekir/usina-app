import streamlit as st
import pandas as pd
from db import get_conn

st.header("Projetos e Ficha Técnica de Produção")

conn = get_conn()
cur = conn.cursor()

# -------------------------
# CADASTRAR MATERIAL
# -------------------------

st.subheader("1. Cadastrar material")

with st.expander("Cadastrar novo material"):
    material_name = st.text_input("Nome do material", placeholder="Ex: Brita 1")
    unit = st.selectbox("Unidade", ["ton", "m3", "L", "saco"])
    low_stock = st.number_input("Estoque mínimo", min_value=0.0, value=0.0)

    if st.button("Salvar material"):
        cur.execute(
            """
            INSERT OR IGNORE INTO items (name, unit, low_stock)
            VALUES (?, ?, ?)
            """,
            (material_name, unit, low_stock),
        )
        conn.commit()
        st.success("Material cadastrado!")
        st.rerun()

# -------------------------
# CADASTRAR PROJETO
# -------------------------

st.subheader("2. Cadastrar projeto")

project_name = st.text_input("Nome do projeto", placeholder="Ex: Projeto 1 - Asfalto Lethem")
client = st.text_input("Cliente")
location = st.text_input("Local")
total_asphalt = st.number_input("Total de asfalto necessário (ton)", min_value=0.0, value=0.0)
status = st.selectbox("Status", ["Planejado", "Em produção", "Concluído"])

if st.button("Salvar projeto"):
    cur.execute(
        """
        INSERT INTO projects
        (name, client, location, total_asphalt_tons, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_name, client, location, total_asphalt, status),
    )
    conn.commit()
    st.success("Projeto cadastrado!")
    st.rerun()

st.divider()

# -------------------------
# SELECIONAR PROJETO
# -------------------------

st.subheader("3. Montar ficha técnica do projeto")

projects = pd.read_sql(
    """
    SELECT id, name, client, location, total_asphalt_tons, status
    FROM projects
    ORDER BY id DESC
    """,
    conn,
)

items = pd.read_sql(
    """
    SELECT id, name, unit
    FROM items
    ORDER BY name
    """,
    conn,
)

if projects.empty:
    st.info("Cadastre um projeto primeiro.")
    conn.close()
    st.stop()

if items.empty:
    st.info("Cadastre materiais primeiro.")
    conn.close()
    st.stop()

projects["label"] = (
    projects["name"]
    + " | "
    + projects["total_asphalt_tons"].astype(str)
    + " ton"
)

selected_project_label = st.selectbox("Selecione o projeto", projects["label"])
selected_project_id = int(projects[projects["label"] == selected_project_label]["id"].iloc[0])

selected_project = projects[projects["id"] == selected_project_id].iloc[0]

st.write(f"**Cliente:** {selected_project['client']}")
st.write(f"**Local:** {selected_project['location']}")
st.write(f"**Total previsto:** {selected_project['total_asphalt_tons']} ton")

st.subheader("Atualizar status do projeto")

current_status = selected_project["status"]

status_options = ["Planejado", "Em produção", "Concluído"]

new_status = st.selectbox(
    "Status atual do projeto",
    status_options,
    index=status_options.index(current_status) if current_status in status_options else 0,
    key="update_project_status"
)

if st.button("Salvar novo status"):
    cur.execute(
        """
        UPDATE projects
        SET status = ?
        WHERE id = ?
        """,
        (new_status, selected_project_id)
    )
    conn.commit()
    st.success("Status do projeto atualizado!")
    st.rerun()

st.divider()

# -------------------------
# ADICIONAR MATERIAL AO PROJETO
# -------------------------

st.subheader("Adicionar material necessário ao projeto")

items["label"] = items["name"] + " (" + items["unit"] + ")"
item_map = dict(zip(items["label"], items["id"]))

selected_item_label = st.selectbox("Material", items["label"])
selected_item_id = item_map[selected_item_label]

planned_qty = st.number_input("Quantidade total necessária para o projeto", min_value=0.0, value=0.0)
unit_cost = st.number_input("Custo unitário estimado", min_value=0.0, value=0.0)

if st.button("Adicionar material ao projeto"):
    cur.execute(
        """
        INSERT INTO project_material_plan
        (project_id, item_id, planned_qty, unit_cost)
        VALUES (?, ?, ?, ?)
        """,
        (selected_project_id, selected_item_id, planned_qty, unit_cost),
    )
    conn.commit()
    st.success("Material adicionado à ficha técnica do projeto!")
    st.rerun()

st.divider()

# -------------------------
# MOSTRAR FICHA TÉCNICA
# -------------------------

st.subheader("Ficha técnica do projeto")

df_plan = pd.read_sql(
    """
    SELECT
        pmp.id,
        i.name AS Material,
        i.unit AS Unidade,
        pmp.planned_qty AS Quantidade_Prevista,
        pmp.unit_cost AS Custo_Unitario,
        (pmp.planned_qty * pmp.unit_cost) AS Custo_Total
    FROM project_material_plan pmp
    JOIN items i ON i.id = pmp.item_id
    WHERE pmp.project_id = ?
    ORDER BY i.name
    """,
    conn,
    params=(selected_project_id,),
)

if df_plan.empty:
    st.info("Nenhum material adicionado a este projeto ainda.")
else:
    st.dataframe(df_plan, use_container_width=True)

    total_cost = df_plan["Custo_Total"].sum()
    st.metric("Custo previsto dos materiais", f"R$ {total_cost:,.2f}")

st.divider()

# -------------------------
# LISTA DE PROJETOS
# -------------------------

st.subheader("Projetos cadastrados")

st.dataframe(projects.drop(columns=["label"]), use_container_width=True)

conn.close()