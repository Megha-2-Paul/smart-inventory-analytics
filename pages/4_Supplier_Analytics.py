import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard_utils import get_data

st.set_page_config(page_title="Supplier Analytics",page_icon="🏭",layout="wide")
st.title("Supplier Analytics")
st.caption("Supplier delivery performance, purchasing volume and lead-time analysis.")
try:
    data=get_data()
except FileNotFoundError as exc:
    st.error(str(exc)); st.stop()

suppliers=data["suppliers"]
orders=data["purchase_orders"].copy()
orders["order_date"]=pd.to_datetime(orders["order_date"])
orders["expected_delivery_date"]=__import__("pandas").to_datetime(orders["expected_delivery_date"])
orders["actual_delivery_date"]=__import__("pandas").to_datetime(orders["actual_delivery_date"])
delivered=orders.loc[orders["status"]=="Delivered"].copy()
delivered["delivery_days"]=(delivered["actual_delivery_date"]-delivered["order_date"]).dt.days
delivered["days_late"]=(delivered["actual_delivery_date"]-delivered["expected_delivery_date"]).dt.days
summary=orders.groupby("supplier_id",as_index=False).agg(purchase_orders=("purchase_order_id","nunique"),units_ordered=("quantity_ordered","sum"),purchase_value=("total_cost","sum"))
delivery=delivered.groupby("supplier_id",as_index=False).agg(delivered_orders=("purchase_order_id","nunique"),average_delivery_days=("delivery_days","mean"),average_days_late=("days_late","mean"))
summary=summary.merge(delivery,on="supplier_id",how="left").merge(suppliers,on="supplier_id",how="left")

a,b,c=st.columns(3)
a.metric("Suppliers",len(suppliers)); b.metric("Purchase orders",len(orders)); c.metric("Delivered orders",len(delivered))
st.subheader("Supplier performance")
st.dataframe(summary[["supplier_name","city","supplier_rating","lead_time_days","purchase_orders","units_ordered","purchase_value","average_delivery_days","average_days_late"]],use_container_width=True,hide_index=True)
left,right=st.columns(2)
with left:
    chart=summary.sort_values("purchase_value",ascending=False).head(12)
    st.plotly_chart(px.bar(chart,x="supplier_name",y="purchase_value",title="Top suppliers by purchase value"),use_container_width=True)
with right:
    st.plotly_chart(px.scatter(summary,x="average_delivery_days",y="supplier_rating",size="purchase_orders",hover_name="supplier_name",title="Supplier rating vs. delivery time"),use_container_width=True)
st.caption("Delivery statistics use purchase orders marked Delivered. All supplier metrics are synthetic.")
