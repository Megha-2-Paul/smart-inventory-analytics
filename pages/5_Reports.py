import streamlit as st
from src.dashboard_utils import get_data,get_inventory_position
from src.inventory_metrics import calculate_kpis,category_performance
from src.stock_alerts import calculate_reorder_recommendations
from src.reporting import build_excel_report,build_pdf_report

st.set_page_config(page_title="Reports & Exports",page_icon="📄",layout="wide")
st.title("Reports & Exports")
st.caption("Generate downloadable inventory, category and replenishment reports.")
try:
    data=get_data()
except FileNotFoundError as exc:
    st.error(str(exc)); st.stop()

inventory=get_inventory_position(data)
kpis=calculate_kpis(inventory,data["sales"])
categories=category_performance(data["sales"],data["products"])
recommendations=calculate_reorder_recommendations(inventory,data["sales"])

left,right=st.columns(2)
with left:
    st.subheader("Excel workbook")
    st.write("Executive KPIs, inventory positions, category performance and reorder recommendations.")
    st.download_button("Download Excel report",build_excel_report(inventory,kpis,categories,recommendations),file_name="smart_inventory_report.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
with right:
    st.subheader("PDF executive report")
    st.write("Headline metrics, priority replenishment items and category performance.")
    st.download_button("Download PDF report",build_pdf_report(kpis,recommendations,categories),file_name="smart_inventory_executive_report.pdf",mime="application/pdf",use_container_width=True)

st.subheader("Inventory snapshot preview")
st.dataframe(inventory.head(25),use_container_width=True,hide_index=True)
st.caption("Reports are generated from synthetic demonstration data. Currency values are illustrative INR amounts.")
