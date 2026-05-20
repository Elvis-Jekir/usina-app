import streamlit as st
import pandas as pd
from db import get_conn

st.header("Manutenção da Frota")

conn = get_conn()
cur = conn.cursor()

equipments = pd.read_sql(
    "SELECT id, name, equipment_type FROM fleet_equipments ORDER BY name",
    conn
)

if equipments.empty:
    st.warning("Cadastre um equipamento primeiro na página Frota.")
    conn.close()
    st.stop()

equipments["label"] = equipments["name"] + " - " + equipments["equipment_type"]
equipment_map = dict(zip(equipments["label"], equipments["id"]))

st.subheader("Registrar manutenção")

equipment_label = st.selectbox("Equipamento", equipments["label"])
equipment_id = equipment_map[equipment_label]

maintenance_date = st.date_input("Data da manutenção")

service_type = st.selectbox(
    "Tipo de serviço",
    ["Troca de óleo", "Filtro", "Pneu", "Revisão", "Correia", "Outro"]
)

description = st.text_area("Descrição")
cost = st.number_input("Custo da manutenção", min_value=0.0, value=0.0)
launch_finance = st.checkbox("Lançar este custo no financeiro agora?")

current_km = st.number_input("KM atual", min_value=0.0, value=0.0)

next_due_date = st.date_input("Próxima manutenção prevista")
next_due_km = st.number_input("Próxima manutenção em KM", min_value=0.0, value=0.0)

st.divider()
st.subheader("Itens usados do estoque da frota")

fleet_items = pd.read_sql(
    """
    SELECT id, name, unit, current_stock
    FROM fleet_stock_items
    ORDER BY name
    """,
    conn
)

use_stock_item = st.checkbox("Usar item do estoque da frota nesta manutenção?")

selected_item_id = None
qty_used = 0

if use_stock_item:
    if fleet_items.empty:
        st.warning("Cadastre itens primeiro em Estoque da Frota.")
    else:
        fleet_items["label"] = (
            fleet_items["name"] + " | estoque: " +
            fleet_items["current_stock"].astype(str) + " " +
            fleet_items["unit"]
        )

        item_map = dict(zip(fleet_items["label"], fleet_items["id"]))

        selected_item_label = st.selectbox("Item usado", fleet_items["label"])
        selected_item_id = item_map[selected_item_label]

        qty_used = st.number_input("Quantidade usada", min_value=0.0, value=0.0)

if st.button("Salvar manutenção"):

    cur.execute(
        """
        INSERT INTO fleet_maintenance
        (equipment_id, maintenance_date, service_type, description, cost,
         current_km, next_due_date, next_due_km)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            equipment_id,
            maintenance_date.isoformat(),
            service_type,
            description,
            cost,
            current_km,
            next_due_date.isoformat(),
            next_due_km,
        ),
    )

    maintenance_id = cur.lastrowid

    if launch_finance and cost > 0:
        cur.execute(
            """
            INSERT INTO financial_movements
            (mov_date, type, category, description, amount)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                maintenance_date.isoformat(),
                "Saída",
                "Manutenção Frota",
                f"{service_type} - {equipment_label}",
                cost,
            ),
        )

    cur.execute(
        """
        UPDATE fleet_equipments
        SET current_km = ?
        WHERE id = ?
        """,
        (current_km, equipment_id),
    )

    if use_stock_item and selected_item_id and qty_used > 0:

        cur.execute(
            """
            INSERT INTO fleet_stock_movements
            (mov_date, item_id, movement_type, qty, equipment_id, maintenance_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                maintenance_date.isoformat(),
                selected_item_id,
                "Saída por manutenção",
                -qty_used,
                equipment_id,
                maintenance_id,
                f"Uso em manutenção: {service_type}",
            ),
        )

        cur.execute(
            """
            UPDATE fleet_stock_items
            SET current_stock = current_stock - ?
            WHERE id = ?
            """,
            (qty_used, selected_item_id),
        )

    conn.commit()

    st.success("Manutenção registrada e estoque atualizado!")
    st.rerun()

st.divider()

st.subheader("Histórico de manutenções")

df = pd.read_sql(
    """
    SELECT 
        fm.maintenance_date AS Data,
        fe.name AS Equipamento,
        fm.service_type AS Servico,
        fm.description AS Descricao,
        fm.cost AS Custo,
        fm.current_km AS KM,
        fm.next_due_date AS Proxima_Data,
        fm.next_due_km AS Proximo_KM
    FROM fleet_maintenance fm
    JOIN fleet_equipments fe ON fe.id = fm.equipment_id
    ORDER BY fm.maintenance_date DESC
    """,
    conn,
)

st.dataframe(df, use_container_width=True)

st.divider()

st.subheader("Histórico de itens usados em manutenção")

df_items = pd.read_sql(
    """
    SELECT
        fsm.mov_date AS Data,
        fe.name AS Equipamento,
        fsi.name AS Item,
        fsm.qty AS Quantidade,
        fsm.notes AS Observacao
    FROM fleet_stock_movements fsm
    JOIN fleet_stock_items fsi ON fsi.id = fsm.item_id
    LEFT JOIN fleet_equipments fe ON fe.id = fsm.equipment_id
    WHERE fsm.movement_type = 'Saída por manutenção'
    ORDER BY fsm.mov_date DESC
    """,
    conn,
)

st.dataframe(df_items, use_container_width=True)

st.divider()

st.subheader("Alertas de Manutenção")

alerts = pd.read_sql(
    """
    SELECT 
        fe.name AS Equipamento,
        fm.service_type AS Servico,
        fm.next_due_date AS Proxima_Data,
        fm.next_due_km AS Proximo_KM,
        fe.current_km AS KM_Atual
    FROM fleet_maintenance fm
    JOIN fleet_equipments fe ON fe.id = fm.equipment_id
    ORDER BY fm.maintenance_date DESC
    """,
    conn,
)

if alerts.empty:
    st.info("Nenhum alerta de manutenção ainda.")
else:

    for _, row in alerts.iterrows():

        if row["Proxima_Data"]:

            days_left = (
                pd.to_datetime(row["Proxima_Data"]) - pd.Timestamp.today()
            ).days

            if days_left < 0:
                st.error(
                    f"{row['Equipamento']} - {row['Servico']} vencido há {abs(days_left)} dias."
                )

            elif days_left <= 7:
                st.warning(
                    f"{row['Equipamento']} - {row['Servico']} vence em {days_left} dias."
                )

        if row["Proximo_KM"] and row["Proximo_KM"] > 0:

            km_left = row["Proximo_KM"] - row["KM_Atual"]

            if km_left <= 0:
                st.error(
                    f"{row['Equipamento']} - {row['Servico']} vencido por KM."
                )

            elif km_left <= 500:
                st.warning(
                    f"{row['Equipamento']} - {row['Servico']} vence em {km_left:.0f} km."
                )

conn.close()