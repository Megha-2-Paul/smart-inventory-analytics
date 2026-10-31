import streamlit as st
import plotly.express as px
from src.dashboard_utils import get_data, get_inventory_position

st.set_page_config(page_title="Inventory Explorer", page_icon="🔎", layout="wide")
st.title("Inventory Explorer")
st.caption("Search, filter and inspect product stock across warehouses.")

try:
    data = get_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

position = get_inventory_position(data)
f1, f2, f3 = st.columns(3)
categories = ["All"] + sorted(position["category"].dropna().unique().tolist())
warehouses = ["All"] + sorted(position["warehouse_id"].dropna().unique().tolist())
statuses = ["All", "Healthy", "Low stock", "Out of stock", "Overstock"]
category = f1.selectbox("Category", categories)
warehouse = f2.selectbox("Warehouse", warehouses)
status = f3.selectbox("Stock status", statuses)
search = st.text_input("Search by SKU or product name")

filtered = position.copy()
if category != "All":
    filtered = filtered.loc[filtered["category"] == category]
if warehouse != "All":
    filtered = filtered.loc[filtered["warehouse_id"] == warehouse]
if status != "All":
    filtered = filtered.loc[filtered["stock_status"] == status]
if search:
    mask = filtered["sku"].str.contains(search, case=False, na=False) | filtered["product_name"].str.contains(search, case=False, na=False)
    filtered = filtered.loc[mask]

a, b, c = st.columns(3)
a.metric("Stock positions", f"{len(filtered):,}")
b.metric("Available units", f"{filtered['available_stock'].sum():,}")
c.metric("Stock cost value", f"₹{filtered['inventory_cost_value'].sum():,.0f}")

st.dataframe(filtered[["sku", "product_name", "category", "warehouse_id", "current_stock", "reserved_stock", "damaged_stock", "available_stock", "reorder_level", "stock_status", "inventory_cost_value"]], use_container_width=True, hide_index=True)
st.subheader("Stock by category")
chart = filtered.groupby("category", as_index=False)["available_stock"].sum().sort_values("available_stock", ascending=False)
st.plotly_chart(px.bar(chart, x="category", y="available_stock", color="available_stock", color_continuous_scale="Teal"), use_container_width=True)
