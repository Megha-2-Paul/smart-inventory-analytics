"""Stock health classification and reorder recommendations."""
from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_reorder_recommendations(
    inventory_position: pd.DataFrame,
    sales: pd.DataFrame,
    *,
    lookback_days: int = 30,
    safety_stock_days: int = 7,
    target_cover_days: int = 30,
    as_of: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Calculate demand-based reorder points and suggested order quantities.

    Average daily demand is calculated from completed sales within the
    lookback window. The recommendation is a planning estimate, not a
    purchase commitment.
    """
    if lookback_days <= 0 or safety_stock_days < 0 or target_cover_days <= 0:
        raise ValueError("Lookback and target cover must be positive; safety days cannot be negative.")

    end = pd.Timestamp(as_of).normalize() if as_of is not None else pd.Timestamp.today().normalize()
    start = end - pd.Timedelta(days=lookback_days - 1)
    recent = sales.loc[
        sales["status"].eq("Completed")
        & pd.to_datetime(sales["order_date"]).between(start, end)
    ].copy()

    demand = recent.groupby(["product_id", "warehouse_id"], as_index=False).agg(
        units_sold=("quantity", "sum")
    )
    demand["average_daily_demand"] = demand["units_sold"] / lookback_days

    result = inventory_position.merge(
        demand[["product_id", "warehouse_id", "units_sold", "average_daily_demand"]],
        on=["product_id", "warehouse_id"], how="left",
        validate="one_to_one",
    )
    result[["units_sold", "average_daily_demand"]] = result[
        ["units_sold", "average_daily_demand"]
    ].fillna(0)

    result["safety_stock"] = np.ceil(
        result["average_daily_demand"] * safety_stock_days
    ).astype(int)
    result["reorder_point"] = np.ceil(
        result["average_daily_demand"] * result["lead_time_days"]
        + result["safety_stock"]
    ).astype(int)
    result["target_stock"] = np.ceil(
        result["average_daily_demand"] * target_cover_days
        + result["safety_stock"]
    ).astype(int)
    result["recommended_order_qty"] = (
        result["target_stock"] - result["available_stock"]
    ).clip(lower=0).astype(int)

    result["alert_level"] = np.select(
        [
            result["available_stock"].eq(0),
            result["available_stock"].le(result["reorder_point"]),
            result["available_stock"].gt(result["reorder_level"] * 5),
        ],
        ["Critical - out of stock", "Reorder", "Review overstock"],
        default="Healthy",
    )
    return result.sort_values(
        ["recommended_order_qty", "average_daily_demand"],
        ascending=False
    ).reset_index(drop=True)


def get_alert_summary(recommendations: pd.DataFrame) -> pd.DataFrame:
    """Count stock positions by alert level."""
    order = ["Critical - out of stock", "Reorder", "Review overstock", "Healthy"]
    counts = recommendations["alert_level"].value_counts().reindex(order, fill_value=0)
    return counts.rename_axis("alert_level").reset_index(name="position_count")
