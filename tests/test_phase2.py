import pandas as pd

from src.inventory_metrics import build_inventory_position, calculate_kpis
from src.stock_alerts import calculate_reorder_recommendations
from src.forecasting import daily_product_demand, moving_average_forecast, random_forest_forecast


def sample_frames():
    products = pd.DataFrame([{
        "product_id": "PRD00001", "sku": "SKU-1", "product_name": "Test item",
        "category": "Electronics", "supplier_id": "SUP00001",
        "unit_cost": 10.0, "selling_price": 20.0,
        "reorder_level": 10, "lead_time_days": 5,
    }])
    inventory = pd.DataFrame([{
        "product_id": "PRD00001", "warehouse_id": "WH00001",
        "current_stock": 8, "reserved_stock": 1, "damaged_stock": 0,
    }])
    dates = pd.date_range("2025-01-01", periods=40, freq="D")
    sales = pd.DataFrame({
        "sales_id": [f"S{i}" for i in range(40)],
        "order_date": dates,
        "product_id": "PRD00001",
        "warehouse_id": "WH00001",
        "quantity": 2,
        "revenue": 40.0,
        "cost_of_goods": 20.0,
        "status": "Completed",
    })
    return products, inventory, sales


def test_inventory_position_and_kpis():
    products, inventory, sales = sample_frames()
    position = build_inventory_position(inventory, products)
    assert position.loc[0, "available_stock"] == 7
    assert position.loc[0, "inventory_cost_value"] == 80
    kpis = calculate_kpis(position, sales)
    assert kpis["product_count"] == 1
    assert kpis["units_sold"] == 80


def test_reorder_recommendation_is_nonnegative():
    products, inventory, sales = sample_frames()
    position = build_inventory_position(inventory, products)
    result = calculate_reorder_recommendations(
        position, sales, lookback_days=30, as_of="2025-02-09"
    )
    assert result.loc[0, "recommended_order_qty"] >= 0
    assert result.loc[0, "reorder_point"] > 0


def test_forecasting_outputs_requested_horizon():
    _, _, sales = sample_frames()
    daily = daily_product_demand(
        sales, "PRD00001", end_date="2025-02-09", history_days=40
    )
    baseline = moving_average_forecast(daily, window=7, horizon=5)
    advanced, mae = random_forest_forecast(daily, horizon=5, lags=7)
    assert len(baseline) == 5
    assert len(advanced) == 5
    assert (baseline["forecast_demand"] >= 0).all()
    assert (advanced["forecast_demand"] >= 0).all()
    assert mae is None or mae >= 0


def test_zero_demand_does_not_create_reorder_when_stock_is_available():
    products, inventory, sales = sample_frames()
    sales["status"] = "Cancelled"
    position = build_inventory_position(inventory, products)

    result = calculate_reorder_recommendations(
        position, sales, lookback_days=30, as_of="2025-02-09"
    )

    assert result.loc[0, "average_daily_demand"] == 0
    assert result.loc[0, "reorder_point"] == 0
    assert result.loc[0, "recommended_order_qty"] == 0


def test_out_of_stock_position_is_marked_critical():
    products, inventory, sales = sample_frames()
    inventory.loc[0, "current_stock"] = 1
    inventory.loc[0, "reserved_stock"] = 1
    inventory.loc[0, "damaged_stock"] = 0
    sales["status"] = "Cancelled"
    position = build_inventory_position(inventory, products)

    result = calculate_reorder_recommendations(
        position, sales, lookback_days=30, as_of="2025-02-09"
    )

    assert result.loc[0, "available_stock"] == 0
    assert result.loc[0, "alert_level"] == "Critical - out of stock"


def test_daily_demand_respects_warehouse_filter():
    _, _, sales = sample_frames()
    second_warehouse = sales.copy()
    second_warehouse["warehouse_id"] = "WH00002"
    second_warehouse["quantity"] = 5
    combined = pd.concat([sales, second_warehouse], ignore_index=True)

    first = daily_product_demand(
        combined, "PRD00001", warehouse_id="WH00001",
        end_date="2025-02-09", history_days=40,
    )
    second = daily_product_demand(
        combined, "PRD00001", warehouse_id="WH00002",
        end_date="2025-02-09", history_days=40,
    )

    assert first["demand"].sum() == 80
    assert second["demand"].sum() == 200
