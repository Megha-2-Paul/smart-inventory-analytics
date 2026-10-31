import streamlit as st
import plotly.express as px
from src.dashboard_utils import get_data, get_inventory_position
from src.stock_alerts import calculate_reorder_recommendations, get_alert_summary

st.set_page_config(page_title="Stock Alerts", page_icon="🚨", layout="wide")
st.title("Stock Alerts & Replenishment")
st.caption("Demand-based reorder recommendations by product and warehouse.")
try:
    data = get_data()
except FileNotFoundError as exc:
    st.error(str(exc)); st.stop()

with st.sidebar:
    st.subheader("Planning assumptions")
    lookback = st.slider("Demand lookback (days)", 7, 90, 30)
    safety_days = st.slider("Safety stock cover (days)", 0, 30, 7)
    target_days = st.slider("Target stock cover (days)", 7, 90, 30)

position = get_inventory_position(data)
recommendations = calculate_reorder_recommendations(position, data["sales"], lookback_days=lookback, safety_stock_days=safety_days, target_cover_days=target_days)
summary = get_alert_summary(recommendations)
counts = dict(zip(summary["alert_level"], summary["position_count"]))

c1,c2,c3,c4=st.columns(4)
c1.metric("Critical stockouts", counts.get("Critical - out of stock",0))
c2.metric("Reorder positions", counts.get("Reorder",0))
c3.metric("Overstock reviews", counts.get("Review overstock",0))
c4.metric("Suggested units to order", f"{recommendations['recommended_order_qty'].sum():,}")

left,right=st.columns([1,1.4])
with left:
    st.plotly_chart(px.bar(summary,x="alert_level",y="position_count",color="alert_level"),use_container_width=True)
with right:
    st.subheader("Highest-priority replenishment")
    priority=recommendations.loc[recommendations["recommended_order_qty"]>0].head(15)
    st.dataframe(priority[["sku","product_name","warehouse_id","available_stock","average_daily_demand","reorder_point","recommended_order_qty","alert_level"]],use_container_width=True,hide_index=True)

st.download_button("Download reorder recommendations (CSV)",recommendations.to_csv(index=False).encode("utf-8"),file_name="reorder_recommendations.csv",mime="text/csv")
