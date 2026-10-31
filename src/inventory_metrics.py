"""Business metrics for inventory health and product performance."""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_inventory_position(inventory: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Join stock snapshots to product attributes and calculate stock value."""
    result = inventory.merge(
        products[["product_id", "sku", "product_name", "category", "supplier_id",
                  "unit_cost", "selling_price", "reorder_level", "lead_time_days"]],
        on="product_id", how="left", validate="many_to_one",
    )
    result["available_stock"] = (
        result["current_stock"] - result["reserved_stock"] - result["damaged_stock"]
    ).clip(lower=0)
    result["inventory_cost_value"] = result["current_stock"] * result["unit_cost"]
    result["inventory_retail_value"] = result["current_stock"] * result["selling_price"]
    result["stock_status"] = np.select(
        [
            result["available_stock"].eq(0),
            result["available_stock"].lt(result["reorder_level"]),
            result["available_stock"].gt(result["reorder_level"] * 5),
        ],
        ["Out of stock", "Low stock", "Overstock"],
        default="Healthy",
    )
    return result


def calculate_kpis(inventory_position: pd.DataFrame, sales: pd.DataFrame) -> dict[str, float | int]:
    """Calculate headline inventory and sales KPIs.

    Sales-based KPIs use completed transactions only. Inventory values use
    the current synthetic stock snapshot.
    """
    completed = sales.loc[sales["status"].eq("Completed")].copy()
    return {
        "product_count": int(inventory_position["product_id"].nunique()),
        "warehouse_count": int(inventory_position["warehouse_id"].nunique()),
        "units_on_hand": int(inventory_position["current_stock"].sum()),
        "available_units": int(inventory_position["available_stock"].sum()),
        "inventory_cost_value": round(float(inventory_position["inventory_cost_value"].sum()), 2),
        "inventory_retail_value": round(float(inventory_position["inventory_retail_value"].sum()), 2),
        "low_stock_positions": int(inventory_position["stock_status"].eq("Low stock").sum()),
        "out_of_stock_positions": int(inventory_position["stock_status"].eq("Out of stock").sum()),
        "completed_sales": int(len(completed)),
        "sales_revenue": round(float(completed["revenue"].sum()), 2),
        "units_sold": int(completed["quantity"].sum()),
    }


def category_performance(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Aggregate completed sales by product category."""
    merged = sales.loc[sales["status"].eq("Completed")].merge(
        products[["product_id", "category"]], on="product_id", how="left"
    )
    return (
        merged.groupby("category", as_index=False)
        .agg(orders=("sales_id", "nunique"), units_sold=("quantity", "sum"),
             revenue=("revenue", "sum"), cost_of_goods=("cost_of_goods", "sum"))
        .assign(gross_profit=lambda x: x["revenue"] - x["cost_of_goods"])
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )


def product_sales_summary(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Rank products using completed sales only."""
    completed = sales.loc[sales["status"].eq("Completed")]
    summary = completed.groupby("product_id", as_index=False).agg(
        orders=("sales_id", "nunique"), units_sold=("quantity", "sum"),
        revenue=("revenue", "sum"), cost_of_goods=("cost_of_goods", "sum")
    )
    summary["gross_profit"] = summary["revenue"] - summary["cost_of_goods"]
    return summary.merge(
        products[["product_id", "sku", "product_name", "category"]],
        on="product_id", how="left", validate="one_to_one"
    ).sort_values("revenue", ascending=False).reset_index(drop=True)
