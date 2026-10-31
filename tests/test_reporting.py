from io import BytesIO
import pandas as pd
from src.reporting import build_excel_report,build_pdf_report


def test_excel_report_is_valid_workbook():
    inventory=pd.DataFrame({"sku":["SKU-1"],"current_stock":[12]})
    categories=pd.DataFrame({"category":["Electronics"],"revenue":[100.0]})
    recommendations=pd.DataFrame({"sku":["SKU-1"],"product_name":["Mouse"],"warehouse_id":["WH00001"],"available_stock":[2],"reorder_point":[5],"recommended_order_qty":[10],"alert_level":["Reorder"]})
    result=build_excel_report(inventory,{"product_count":1},categories,recommendations)
    workbook=pd.ExcelFile(BytesIO(result))
    assert set(workbook.sheet_names)=={"Executive Summary","Inventory","Category Performance","Reorder Recommendations"}


def test_pdf_report_has_pdf_signature():
    categories=pd.DataFrame({"category":["Electronics"],"orders":[2],"units_sold":[5],"revenue":[100.0],"gross_profit":[30.0]})
    recommendations=pd.DataFrame({"sku":["SKU-1"],"product_name":["Mouse"],"warehouse_id":["WH00001"],"available_stock":[2],"reorder_point":[5],"recommended_order_qty":[10],"alert_level":["Reorder"]})
    result=build_pdf_report({"product_count":1},recommendations,categories)
    assert result.startswith(b"%PDF")
