import streamlit as st
import pandas as pd
from db import get_conn

st.header("Financeiro / Fluxo de Caixa")

conn = get_conn()
cur = conn.cursor()

# -------------------------
# DADOS BASE
# -------------------------

items = pd.read_sql("SELECT id, name, unit FROM items ORDER BY name", conn)
projects = pd.read_sql("SELECT id, name FROM projects ORDER BY name", conn)

project_options = ["Sem projeto"]
project_map = {"Sem projeto": None}

if not projects.empty:
    for _, row in projects.iterrows():
        project_options.append(row["name"])
        project_map[row["name"]] = int(row["id"])

# -------------------------
# NOVA MOVIMENTAÇÃO
# -------------------------

st.subheader("Nova movimentação financeira")

tipo_mov = st.selectbox(
    "Tipo de movimentação",
    ["Entrada", "Saída"]
)

categoria = st.selectbox(
    "Categoria",
    [
        "Venda",
        "Compra de Materiais",
        "Compra Estoque Frota",
        "Combustível",
        "Alimentação",
        "Funcionários",
        "Manutenção",
        "Luz",
        "Internet",
        "Outros"
    ]
)

project_label = st.selectbox("Projeto relacionado", project_options)
project_id = project_map[project_label]

data_mov = st.date_input("Data")
descricao = st.text_input("Descrição")

# -------------------------
# COMPRA DE MATERIAIS
# -------------------------

if categoria == "Compra de Materiais":

    st.info("Esta compra será lançada no financeiro e também dará entrada no estoque.")

    if items.empty:
        st.warning("Cadastre materiais primeiro.")
        conn.close()
        st.stop()

    items["label"] = items["name"] + " (" + items["unit"] + ")"
    item_map = dict(zip(items["label"], items["id"]))

    selected_item = st.selectbox("Material comprado", items["label"])
    item_id = item_map[selected_item]

    unidade = items[items["id"] == item_id]["unit"].iloc[0]

    quantidade = st.number_input(f"Quantidade comprada ({unidade})", min_value=0.0, value=0.0)
    valor_total = st.number_input("Valor total da compra", min_value=0.0, value=0.0)
    fornecedor = st.text_input("Fornecedor")

    custo_unitario = valor_total / quantidade if quantidade > 0 else 0

    st.metric("Custo unitário calculado", f"R$ {custo_unitario:,.2f}")

    if st.button("Registrar compra de material"):

        if quantidade <= 0 or valor_total <= 0:
            st.error("Informe quantidade e valor total maiores que zero.")
            conn.close()
            st.stop()

        # Financeiro
        cur.execute("""
            INSERT INTO financial_movements
            (mov_date, type, category, description, amount, project_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data_mov.isoformat(),
            "Saída",
            "Compra de Materiais",
            descricao if descricao else f"Compra de {selected_item}",
            valor_total,
            project_id
        ))

        # Histórico da compra
        cur.execute("""
            INSERT INTO material_purchases
            (purchase_date, item_id, qty, unit, total_value, unit_cost, project_id, supplier, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data_mov.isoformat(),
            item_id,
            quantidade,
            unidade,
            valor_total,
            custo_unitario,
            project_id,
            fornecedor,
            descricao
        ))

        purchase_id = cur.lastrowid

        # Entrada no estoque
        cur.execute("""
            INSERT INTO stock_movements
            (mov_date, item_id, qty, ref_type, ref_id, project_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data_mov.isoformat(),
            item_id,
            quantidade,
            "purchase",
            purchase_id,
            project_id,
            f"Compra de material: {selected_item}"
        ))

        # Atualiza custo unitário atual
        cur.execute("""
            UPDATE items
            SET unit_cost = ?
            WHERE id = ?
        """, (
            custo_unitario,
            item_id
        ))

        conn.commit()
        st.success("Compra registrada no financeiro e estoque atualizado!")
        st.rerun()

# -------------------------
# COMPRA ESTOQUE FROTA
# -------------------------

elif categoria == "Compra Estoque Frota":

    st.info("Esta compra será lançada no financeiro e também dará entrada no estoque da frota.")

    fleet_items = pd.read_sql("""
        SELECT id, name, unit
        FROM fleet_stock_items
        ORDER BY name
    """, conn)

    if fleet_items.empty:
        st.warning("Cadastre itens primeiro em Estoque Frota.")
        conn.close()
        st.stop()

    fleet_items["label"] = fleet_items["name"] + " (" + fleet_items["unit"] + ")"

    fleet_item_map = dict(zip(fleet_items["label"], fleet_items["id"]))

    selected_item = st.selectbox(
        "Item comprado",
        fleet_items["label"]
    )

    item_id = fleet_item_map[selected_item]

    unidade = fleet_items[fleet_items["id"] == item_id]["unit"].iloc[0]

    quantidade = st.number_input(
        f"Quantidade comprada ({unidade})",
        min_value=0.0,
        value=0.0,
        key="frota_qty"
    )

    valor_total = st.number_input(
        "Valor total da compra",
        min_value=0.0,
        value=0.0,
        key="frota_valor"
    )

    fornecedor = st.text_input("Fornecedor", key="frota_fornecedor")

    custo_unitario = valor_total / quantidade if quantidade > 0 else 0

    st.metric(
        "Custo unitário calculado",
        f"R$ {custo_unitario:,.2f}"
    )

    if st.button("Registrar compra estoque frota"):

        # financeiro
        cur.execute("""
            INSERT INTO financial_movements
            (mov_date, type, category, description, amount)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data_mov.isoformat(),
            "Saída",
            "Compra Estoque Frota",
            descricao if descricao else f"Compra de {selected_item}",
            valor_total
        ))

        # entrada estoque frota
        cur.execute("""
            UPDATE fleet_stock_items
            SET current_stock = current_stock + ?,
                unit_cost = ?
            WHERE id = ?
        """, (
            quantidade,
            custo_unitario,
            item_id
        ))

        # histórico movimentação
        cur.execute("""
            INSERT INTO fleet_stock_movements
            (mov_date, item_id, movement_type, qty, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data_mov.isoformat(),
            item_id,
            "Compra",
            quantidade,
            f"Fornecedor: {fornecedor}"
        ))

        conn.commit()

        st.success("Compra registrada e estoque da frota atualizado!")

        st.rerun()

# -------------------------
# OUTRAS MOVIMENTAÇÕES
# -------------------------

else:

    valor = st.number_input("Valor", min_value=0.0, value=0.0)

    if st.button("Registrar movimentação"):

        if valor <= 0:
            st.error("Informe um valor maior que zero.")
            conn.close()
            st.stop()

        cur.execute("""
            INSERT INTO financial_movements
            (mov_date, type, category, description, amount, project_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data_mov.isoformat(),
            tipo_mov,
            categoria,
            descricao,
            valor,
            project_id
        ))

        conn.commit()
        st.success("Movimentação registrada!")
        st.rerun()

st.divider()

# -------------------------
# HISTÓRICO FINANCEIRO
# -------------------------

st.subheader("Histórico financeiro")

df = pd.read_sql("""
SELECT
    fm.mov_date AS Data,
    fm.type AS Tipo,
    fm.category AS Categoria,
    fm.description AS Descricao,
    fm.amount AS Valor,
    p.name AS Projeto
FROM financial_movements fm
LEFT JOIN projects p ON p.id = fm.project_id
ORDER BY fm.id DESC
""", conn)

if df.empty:
    st.info("Nenhuma movimentação financeira registrada.")
else:
    df["Data"] = pd.to_datetime(df["Data"])

    col1, col2, col3 = st.columns(3)

    with col1:
        filtro_periodo = st.selectbox(
            "Período",
            ["Todos", "Hoje", "Últimos 7 dias", "Este mês", "Escolher datas"]
        )

    with col2:
        filtro_tipo = st.selectbox(
            "Tipo",
            ["Todos", "Entrada", "Saída"]
        )

    with col3:
        categorias = ["Todas"] + sorted(df["Categoria"].dropna().unique().tolist())
        filtro_categoria = st.selectbox("Categoria", categorias)

    df_filtrado = df.copy()

    hoje = pd.Timestamp.today().normalize()

    if filtro_periodo == "Hoje":
        df_filtrado = df_filtrado[df_filtrado["Data"].dt.normalize() == hoje]

    elif filtro_periodo == "Últimos 7 dias":
        inicio = hoje - pd.Timedelta(days=7)
        df_filtrado = df_filtrado[df_filtrado["Data"] >= inicio]

    elif filtro_periodo == "Este mês":
        df_filtrado = df_filtrado[
            (df_filtrado["Data"].dt.month == hoje.month) &
            (df_filtrado["Data"].dt.year == hoje.year)
        ]

    elif filtro_periodo == "Escolher datas":
        c1, c2 = st.columns(2)
        with c1:
            data_inicio = st.date_input("Data inicial")
        with c2:
            data_fim = st.date_input("Data final")

        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)

        df_filtrado = df_filtrado[
            (df_filtrado["Data"] >= data_inicio) &
            (df_filtrado["Data"] <= data_fim)
        ]

    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]

    if filtro_categoria != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Categoria"] == filtro_categoria]

    total_entradas = df_filtrado[df_filtrado["Tipo"] == "Entrada"]["Valor"].sum()
    total_saidas = df_filtrado[df_filtrado["Tipo"] == "Saída"]["Valor"].sum()
    saldo_periodo = total_entradas - total_saidas

    m1, m2, m3 = st.columns(3)
    m1.metric("Entradas no período", f"R$ {total_entradas:,.2f}")
    m2.metric("Saídas no período", f"R$ {total_saidas:,.2f}")
    m3.metric("Saldo do período", f"R$ {saldo_periodo:,.2f}")

    st.dataframe(df_filtrado, use_container_width=True)

st.divider()

# -------------------------
# HISTÓRICO DE COMPRAS
# -------------------------

st.subheader("Histórico de compras de materiais")

df_purchases = pd.read_sql("""
SELECT
    mp.purchase_date AS Data,
    i.name AS Material,
    mp.qty AS Quantidade,
    mp.unit AS Unidade,
    mp.total_value AS Valor_Total,
    mp.unit_cost AS Custo_Unitario,
    mp.supplier AS Fornecedor,
    p.name AS Projeto
FROM material_purchases mp
JOIN items i ON i.id = mp.item_id
LEFT JOIN projects p ON p.id = mp.project_id
ORDER BY mp.id DESC
""", conn)

if df_purchases.empty:
    st.info("Nenhuma compra de material registrada.")
else:
    col1, col2 = st.columns(2)

    with col1:
        materiais = ["Todos"] + sorted(df_purchases["Material"].dropna().unique().tolist())
        filtro_material = st.selectbox("Filtrar por material", materiais)

    with col2:
        ordenar = st.selectbox(
            "Ordenar",
            [
                "Mais recentes",
                "Mais antigas",
                "Material A-Z",
                "Material Z-A",
                "Maior valor",
                "Menor valor",
            ]
        )

    df_filtrado = df_purchases.copy()

    if filtro_material != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Material"] == filtro_material]

    if ordenar == "Mais recentes":
        df_filtrado = df_filtrado.sort_values("Data", ascending=False)
    elif ordenar == "Mais antigas":
        df_filtrado = df_filtrado.sort_values("Data", ascending=True)
    elif ordenar == "Material A-Z":
        df_filtrado = df_filtrado.sort_values("Material", ascending=True)
    elif ordenar == "Material Z-A":
        df_filtrado = df_filtrado.sort_values("Material", ascending=False)
    elif ordenar == "Maior valor":
        df_filtrado = df_filtrado.sort_values("Valor_Total", ascending=False)
    elif ordenar == "Menor valor":
        df_filtrado = df_filtrado.sort_values("Valor_Total", ascending=True)

    st.dataframe(df_filtrado, use_container_width=True)