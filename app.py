import streamlit as st

st.set_page_config(
    page_title="Smart Inventory Analytics",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Smart Inventory Analytics")
st.caption("E-commerce inventory monitoring and decision support")

st.info(
    "Project foundation is ready. Generate the sample datasets with "
    "`python -m src.data_generator` before using the analytics pages."
)

st.subheader("Project configuration")
col1, col2, col3 = st.columns(3)
col1.metric("Products planned", "500")
col2.metric("Warehouses planned", "5")
col3.metric("Sales transactions planned", "12,000")
