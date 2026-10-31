"""Export inventory analytics to Excel and PDF."""
from __future__ import annotations

from io import BytesIO
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def build_excel_report(
    inventory: pd.DataFrame,
    kpis: dict,
    category_summary: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> bytes:
    """Create a multi-sheet Excel workbook and return its bytes."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([kpis]).to_excel(writer, sheet_name="Executive Summary", index=False)
        inventory.to_excel(writer, sheet_name="Inventory", index=False)
        category_summary.to_excel(writer, sheet_name="Category Performance", index=False)
        recommendations.to_excel(writer, sheet_name="Reorder Recommendations", index=False)

        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for column_cells in worksheet.columns:
                values = [len(str(cell.value or "")) for cell in column_cells[:200]]
                width = min(max(max(values, default=10) + 2, 12), 36)
                worksheet.column_dimensions[column_cells[0].column_letter].width = width

    return output.getvalue()


def build_pdf_report(kpis: dict, recommendations: pd.DataFrame, category_summary: pd.DataFrame) -> bytes:
    """Create a concise printable PDF executive report."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=landscape(A4),
        rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Smart Inventory Analytics", styles["Title"]),
        Paragraph(f"Executive inventory report | Generated {datetime.now():%d %b %Y, %H:%M}", styles["Normal"]),
        Spacer(1, 14),
    ]

    summary_rows = [["Metric", "Value"]]
    labels = {
        "product_count": "Products",
        "warehouse_count": "Warehouses",
        "units_on_hand": "Units on hand",
        "available_units": "Available units",
        "inventory_cost_value": "Inventory cost value",
        "low_stock_positions": "Low-stock positions",
        "out_of_stock_positions": "Out-of-stock positions",
        "sales_revenue": "Completed sales revenue",
    }
    for key, label in labels.items():
        value = kpis.get(key, 0)
        if "value" in key or key == "sales_revenue":
            value = f"INR {float(value):,.2f}"
        summary_rows.append([label, str(value)])

    summary_table = Table(summary_rows, colWidths=[210, 180], repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E1EA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6F9")]),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([Paragraph("Executive summary", styles["Heading2"]), summary_table, Spacer(1, 16)])

    story.append(Paragraph("Priority reorder recommendations", styles["Heading2"]))
    cols = ["sku", "product_name", "warehouse_id", "available_stock", "reorder_point", "recommended_order_qty", "alert_level"]
    available_cols = [c for c in cols if c in recommendations.columns]
    top = recommendations.loc[recommendations.get("recommended_order_qty", pd.Series(dtype=float)).gt(0), available_cols].head(15)
    table_data = [available_cols] + top.fillna("").astype(str).values.tolist() if available_cols else [["No recommendation data"]]
    reorder_table = Table(table_data, repeatRows=1)
    reorder_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E1EA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6F9")]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([reorder_table, Spacer(1, 16)])

    story.append(Paragraph("Category performance", styles["Heading2"]))
    category_cols = [c for c in ["category", "orders", "units_sold", "revenue", "gross_profit"] if c in category_summary.columns]
    category_data = [category_cols] + category_summary[category_cols].head(10).round(2).astype(str).values.tolist() if category_cols else [["No category data"]]
    category_table = Table(category_data, repeatRows=1)
    category_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E1EA")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(category_table)

    document.build(story)
    return output.getvalue()
