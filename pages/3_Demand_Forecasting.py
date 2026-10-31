import streamlit as st
import plotly.express as px
import pandas as pd
from src.dashboard_utils import get_data
from src.forecasting import daily_product_demand, moving_average_forecast, random_forest_forecast

st.set_page_config(page_title="Demand Forecasting", page_icon="📈", layout="wide")
st.title("Demand Forecasting")
st.caption("Compare a moving-average baseline with a Random Forest model.")
try:
    data=get_data()
except FileNotFoundError as exc:
    st.error(str(exc)); st.stop()

products=data["products"].sort_values("sku")
sku=st.selectbox("Select product",products["sku"].tolist())
product=products.loc[products["sku"]==sku].iloc[0]
warehouse_options=["All warehouses"]+sorted(data["warehouses"]["warehouse_id"].tolist())
warehouse_choice=st.selectbox("Warehouse",warehouse_options)
history_days=st.slider("Historical window (days)",60,365,180)
horizon=st.slider("Forecast horizon (days)",7,30,14)
window=st.slider("Moving average window",3,30,7)
warehouse_id=None if warehouse_choice=="All warehouses" else warehouse_choice

daily=daily_product_demand(data["sales"],product["product_id"],warehouse_id=warehouse_id,history_days=history_days)
if daily["demand"].sum()==0:
    st.warning("No completed sales for this product in the selected history window. Choose another product."); st.stop()

baseline=moving_average_forecast(daily,window=window,horizon=horizon)
with st.spinner("Training Random Forest forecast..."):
    advanced,mae=random_forest_forecast(daily,horizon=horizon,lags=14)

historical=daily.rename(columns={"demand":"units"}).assign(series="Historical")
baseline_plot=baseline.rename(columns={"forecast_demand":"units"}).assign(series="Moving average")
advanced_plot=advanced.rename(columns={"forecast_demand":"units"}).assign(series="Random Forest")
plot_data=pd.concat([historical[["date","units","series"]],baseline_plot[["date","units","series"]],advanced_plot[["date","units","series"]]])

a,b,c=st.columns(3)
a.metric("Historical units",f"{daily['demand'].sum():,.0f}")
b.metric("Moving average forecast",f"{baseline['forecast_demand'].sum():,.1f}")
c.metric("Random Forest holdout MAE","N/A" if mae is None else f"{mae:.2f} units")
st.plotly_chart(px.line(plot_data,x="date",y="units",color="series"),use_container_width=True)
st.subheader("Forecast values")
comparison=baseline.merge(advanced,on="date",suffixes=("_moving_average","_random_forest"))
st.dataframe(comparison.round(2),use_container_width=True,hide_index=True)
st.caption("Forecasts are estimates trained on synthetic sales history. Holdout MAE is a historical evaluation metric, not a guarantee of future accuracy.")
