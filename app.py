from __future__ import annotations

import streamlit as st
import plotly.express as px

from src.dashboard_utils import get_data, get_inventory_position, format_currency
from src.inventory_metrics import calculate_kpis, category_performance
from src.stock_alerts import calculate_reorder_recommendations

st.set_page_config(page_title="Smart Inventory Analytics", page_icon="📦", layout="wide")

st.markdown("""
<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {background: #111f33; border: 1px solid #263b55; padding: 16px; border-radius: 12px;}
    div[data-testid="stMetricLabel"] p {color: #a9bdd2;}
</style>
""", unsafe_allow_html=True)

st.title("📦 Smart Inventory Analytics")
st.caption("E-commerce inventory intelligence | Executive overview")

try:
    data = get_data()
except FileNotFoundError as exc:
    st.warning(str(exc))
    st.code("python -m src.data_generator\nstreamlit run app.py", language="powershell")
    st.stop()

inventory = get_inventory_position(data)
kpis = calculate_kpis(inventory, data["sales"])
recommendations = calculate_reorder_recommendations(inventory, data["sales"])
categories = category_performance(data["sales"], data["products"])

st.sidebar.success("Synthetic demo data loaded")
st.sidebar.caption("All figures are generated sample data.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Products", f"{kpis['product_count']:,}")
c2.metric("Units on hand", f"{kpis['units_on_hand']:,}")
c3.metric("Inventory cost value", format_currency(kpis["inventory_cost_value"]))
c4.metric("Completed sales revenue", format_currency(kpis["sales_revenue"]))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Warehouses", kpis["warehouse_count"])
c6.metric("Available units", f"{kpis['available_units']:,}")
c7.metric("Low-stock positions", f"{kpis['low_stock_positions']:,}")
c8.metric("Out of stock", f"{kpis['out_of_stock_positions']:,}")

left, right = st.columns([1.15, 1])
with left:
    st.subheader("Inventory health")
    health = inventory["stock_status"].value_counts().rename_axis("status").reset_index(name="positions")
    fig = px.pie(health, names="status", values="positions", hole=.58,
                 color_discrete_sequence=["#14B8A6", "#F59E0B", "#EF4444", "#64748B"])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend_title="")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue by category")
    fig = px.bar(categories.sort_values("revenue"), x="revenue", y="category", orientation="h",
                 color="gross_profit", color_continuous_scale="Tealgrn")
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Revenue (INR)", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Products requiring attention")
priority = recommendations.loc[recommendations["recommended_order_qty"] > 0].head(12)
display_cols = ["sku", "product_name", "warehouse_id", "available_stock", "reorder_point", "recommended_order_qty", "alert_level"]
st.dataframe(priority[display_cols], use_container_width=True, hide_index=True)

st.caption("Planning estimates use completed sales and synthetic inventory snapshots. Validate recommendations before purchasing.")
