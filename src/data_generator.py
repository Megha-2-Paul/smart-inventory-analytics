"""Generate reproducible synthetic e-commerce inventory datasets.

Run from the project root:
    python -m src.data_generator
    python -m src.data_generator --seed 42 --days 365
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "raw"

NUM_PRODUCTS = 500
NUM_SUPPLIERS = 50
NUM_WAREHOUSES = 5
NUM_SALES = 12_000
NUM_PURCHASE_ORDERS = 1_000

CATEGORIES = {
    "Electronics": ["Wireless Mouse", "Mechanical Keyboard", "Bluetooth Speaker", "USB Hub", "Webcam", "Power Bank", "Headphones", "Smart Watch"],
    "Home & Kitchen": ["Coffee Maker", "Air Fryer", "Water Bottle", "Storage Container", "Electric Kettle", "Kitchen Scale", "Desk Lamp"],
    "Fashion": ["Cotton T-Shirt", "Running Shoes", "Backpack", "Wrist Watch", "Sunglasses", "Leather Wallet"],
    "Sports & Fitness": ["Yoga Mat", "Resistance Bands", "Dumbbells", "Fitness Tracker", "Skipping Rope", "Gym Bag"],
    "Beauty & Personal Care": ["Face Wash", "Hair Dryer", "Skin Moisturizer", "Electric Trimmer", "Sunscreen", "Hair Serum"],
    "Office Supplies": ["Notebook", "Office Chair", "Desk Organizer", "Printer Paper", "Wireless Presenter", "Pen Set"],
}
BRANDS = ["NovaTech", "UrbanNest", "PrimeGoods", "EcoLiving", "SmartEdge", "DailyEssentials", "NextWave", "CorePlus", "BrightLife", "FlexiStore"]
CITIES = ["Kolkata", "Mumbai", "Delhi", "Bengaluru", "Chennai"]
WAREHOUSE_NAMES = ["Kolkata Central Warehouse", "Mumbai Distribution Center", "Delhi Fulfillment Hub", "Bengaluru Storage Facility", "Chennai Logistics Center"]
SUPPLIER_PREFIXES = ["Global Supply", "Prime Distribution", "Urban Wholesale", "NextGen Suppliers", "Reliable Traders", "Metro Supply", "Eastern Commerce", "National Distributors", "Smart Procurement", "Universal Retail"]


def ids(prefix: str, count: int) -> list[str]:
    return [f"{prefix}{i:05d}" for i in range(1, count + 1)]


def random_dates(rng: np.random.Generator, start: pd.Timestamp, end: pd.Timestamp, size: int) -> pd.DatetimeIndex:
    start_s, end_s = start.value // 10**9, end.value // 10**9
    return pd.to_datetime(rng.integers(start_s, end_s + 1, size=size), unit="s").normalize()


def generate_suppliers(rng: np.random.Generator) -> pd.DataFrame:
    return pd.DataFrame({
        "supplier_id": ids("SUP", NUM_SUPPLIERS),
        "supplier_name": [f"{rng.choice(SUPPLIER_PREFIXES)} {i+1} Ltd." for i in range(NUM_SUPPLIERS)],
        "contact_email": [f"supplier{i+1}@example.com" for i in range(NUM_SUPPLIERS)],
        "city": rng.choice(CITIES, NUM_SUPPLIERS),
        "lead_time_days": rng.integers(3, 21, NUM_SUPPLIERS),
        "supplier_rating": np.round(rng.uniform(2.8, 5.0, NUM_SUPPLIERS), 1),
        "payment_terms": rng.choice(["Net 15", "Net 30", "Net 45", "Net 60"], NUM_SUPPLIERS),
        "is_active": rng.choice([True, False], NUM_SUPPLIERS, p=[0.92, 0.08]),
    })


def generate_warehouses() -> pd.DataFrame:
    return pd.DataFrame({
        "warehouse_id": ids("WH", NUM_WAREHOUSES),
        "warehouse_name": WAREHOUSE_NAMES,
        "city": CITIES,
        "storage_capacity": [10_000, 15_000, 12_000, 18_000, 14_000],
        "warehouse_type": ["Central", "Distribution", "Fulfillment", "Storage", "Distribution"],
    })


def generate_products(rng: np.random.Generator, suppliers: pd.DataFrame, end_date: pd.Timestamp) -> pd.DataFrame:
    categories = list(CATEGORIES)
    selected_categories = rng.choice(categories, NUM_PRODUCTS)
    names = [rng.choice(CATEGORIES[c]) for c in selected_categories]
    cost = np.round(rng.uniform(100, 8_000, NUM_PRODUCTS), 2)
    price = np.round(cost * rng.uniform(1.15, 2.0, NUM_PRODUCTS), 2)
    return pd.DataFrame({
        "product_id": ids("PRD", NUM_PRODUCTS),
        "sku": [f"SKU-{10000+i}" for i in range(NUM_PRODUCTS)],
        "product_name": names,
        "category": selected_categories,
        "brand": rng.choice(BRANDS, NUM_PRODUCTS),
        "supplier_id": rng.choice(suppliers["supplier_id"], NUM_PRODUCTS),
        "unit_cost": cost,
        "selling_price": price,
        "reorder_level": rng.integers(10, 100, NUM_PRODUCTS),
        "lead_time_days": rng.integers(3, 21, NUM_PRODUCTS),
        "launch_date": random_dates(
            rng,
            end_date - pd.Timedelta(days=700),
            end_date - pd.Timedelta(days=30),
            NUM_PRODUCTS,
        ),
        "is_active": rng.choice([True, False], NUM_PRODUCTS, p=[0.95, 0.05]),
    })


def generate_inventory(rng: np.random.Generator, products: pd.DataFrame, warehouses: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    rows = []
    for p in products.itertuples(index=False):
        for w in warehouses.itertuples(index=False):
            level = int(p.reorder_level)
            scenario = rng.choice(["healthy", "low", "out", "overstock"], p=[0.65, 0.20, 0.05, 0.10])
            if scenario == "healthy":
                stock = int(rng.integers(max(1, level), max(level + 1, level * 5)))
            elif scenario == "low":
                stock = int(rng.integers(1, max(2, level)))
            elif scenario == "out":
                stock = 0
            else:
                stock = int(rng.integers(max(1, level * 5), max(2, level * 12)))
            reserved = int(rng.integers(0, min(stock, 20) + 1))
            damaged = int(rng.integers(0, min(stock - reserved, 3) + 1))
            rows.append({
                "product_id": p.product_id,
                "warehouse_id": w.warehouse_id,
                "current_stock": stock,
                "reserved_stock": reserved,
                "damaged_stock": damaged,
                "last_restocked": as_of - pd.Timedelta(days=int(rng.integers(1, 90))),
            })
    return pd.DataFrame(rows)


def generate_sales(rng: np.random.Generator, products: pd.DataFrame, warehouses: pd.DataFrame, end_date: pd.Timestamp, days: int) -> pd.DataFrame:
    product_weights = rng.pareto(2.0, NUM_PRODUCTS) + 0.5
    product_weights /= product_weights.sum()
    product_ids = rng.choice(products["product_id"].to_numpy(), NUM_SALES, p=product_weights)
    lookup = products.set_index("product_id")
    qty = rng.choice([1, 2, 3, 4, 5, 6, 10], NUM_SALES, p=[.32, .24, .16, .12, .08, .05, .03])
    dates = random_dates(rng, end_date - pd.Timedelta(days=days - 1), end_date, NUM_SALES)
    seasonal = np.where(np.isin(dates.month, [10, 11, 12]), 1.25, 1.0)
    qty = np.maximum(1, np.round(qty * seasonal).astype(int))
    price = lookup.loc[product_ids, "selling_price"].to_numpy()
    cost = lookup.loc[product_ids, "unit_cost"].to_numpy()
    discount = rng.choice([0, .05, .10, .15, .20], NUM_SALES, p=[.40, .25, .18, .12, .05])
    status = rng.choice(["Completed", "Returned", "Cancelled"], NUM_SALES, p=[.93, .04, .03])
    return pd.DataFrame({
        "sales_id": ids("SAL", NUM_SALES),
        "order_date": dates,
        "product_id": product_ids,
        "warehouse_id": rng.choice(warehouses["warehouse_id"].to_numpy(), NUM_SALES),
        "quantity": qty,
        "unit_price": price,
        "unit_cost": cost,
        "discount_pct": discount,
        "revenue": np.round(qty * price * (1 - discount), 2),
        "cost_of_goods": np.round(qty * cost, 2),
        "status": status,
        "sales_channel": rng.choice(["Website", "Mobile App", "Marketplace"], NUM_SALES, p=[.45, .30, .25]),
        "payment_method": rng.choice(["Card", "UPI", "Net Banking", "COD"], NUM_SALES),
    }).sort_values("order_date").reset_index(drop=True)


def generate_purchase_orders(rng: np.random.Generator, products: pd.DataFrame, suppliers: pd.DataFrame, warehouses: pd.DataFrame, end_date: pd.Timestamp) -> pd.DataFrame:
    product_ids = rng.choice(products["product_id"].to_numpy(), NUM_PURCHASE_ORDERS)
    product_lookup = products.set_index("product_id")
    supplier_ids = product_lookup.loc[product_ids, "supplier_id"].to_numpy()
    order_dates = random_dates(rng, end_date - pd.Timedelta(days=365), end_date - pd.Timedelta(days=30), NUM_PURCHASE_ORDERS)
    costs = product_lookup.loc[product_ids, "unit_cost"].to_numpy()
    qty = rng.integers(20, 300, NUM_PURCHASE_ORDERS)
    status = rng.choice(["Delivered", "Pending", "In Transit", "Cancelled"], NUM_PURCHASE_ORDERS, p=[.65, .15, .15, .05])
    supplier_lookup = suppliers.set_index("supplier_id")
    lead = supplier_lookup.loc[supplier_ids, "lead_time_days"].to_numpy()
    expected = order_dates + pd.to_timedelta(lead, unit="D")
    actual = [
        expected_date + pd.Timedelta(days=int(rng.integers(-2, 8)))
        if state == "Delivered" and expected_date + pd.Timedelta(days=7) <= end_date
        else (min(end_date, expected_date) if state == "Delivered" else pd.NaT)
        for state, expected_date in zip(status, expected)
    ]
    return pd.DataFrame({
        "purchase_order_id": ids("PO", NUM_PURCHASE_ORDERS),
        "product_id": product_ids,
        "supplier_id": supplier_ids,
        "warehouse_id": rng.choice(warehouses["warehouse_id"].to_numpy(), NUM_PURCHASE_ORDERS),
        "order_date": order_dates,
        "expected_delivery_date": expected,
        "actual_delivery_date": actual,
        "quantity_ordered": qty,
        "unit_cost": costs,
        "total_cost": np.round(qty * costs, 2),
        "status": status,
    })


def validate_datasets(data: dict[str, pd.DataFrame]) -> None:
    products, suppliers = data["products"], data["suppliers"]
    warehouses, inventory = data["warehouses"], data["inventory"]
    sales, purchase_orders = data["sales"], data["purchase_orders"]

    for frame, key in [
        (products, "product_id"), (suppliers, "supplier_id"),
        (warehouses, "warehouse_id"), (sales, "sales_id"),
        (purchase_orders, "purchase_order_id"),
    ]:
        assert frame[key].is_unique, f"Duplicate primary key: {key}"

    assert products["supplier_id"].isin(suppliers["supplier_id"]).all()
    assert inventory["product_id"].isin(products["product_id"]).all()
    assert inventory["warehouse_id"].isin(warehouses["warehouse_id"]).all()
    assert sales["product_id"].isin(products["product_id"]).all()
    assert sales["warehouse_id"].isin(warehouses["warehouse_id"]).all()
    assert purchase_orders["product_id"].isin(products["product_id"]).all()
    assert purchase_orders["supplier_id"].isin(suppliers["supplier_id"]).all()
    assert purchase_orders["warehouse_id"].isin(warehouses["warehouse_id"]).all()

    assert not inventory.duplicated(["product_id", "warehouse_id"]).any()
    assert (products["unit_cost"] > 0).all()
    assert (products["selling_price"] > products["unit_cost"]).all()
    assert (inventory["current_stock"] >= 0).all()
    assert (inventory["reserved_stock"] <= inventory["current_stock"]).all()
    assert (sales["quantity"] > 0).all()
    assert sales["discount_pct"].between(0, 1).all()

    delivered = purchase_orders[purchase_orders["status"] == "Delivered"]
    assert delivered["actual_delivery_date"].notna().all()
    assert (delivered["actual_delivery_date"] <= pd.Timestamp.today().normalize()).all()


def generate_all_datasets(seed: int = 42, history_days: int = 365) -> dict[str, pd.DataFrame]:
    if history_days < 30:
        raise ValueError("History period must be at least 30 days.")

    rng = np.random.default_rng(seed)
    end_date = pd.Timestamp.today().normalize()

    suppliers = generate_suppliers(rng)
    warehouses = generate_warehouses()
    products = generate_products(rng, suppliers, end_date)
    inventory = generate_inventory(rng, products, warehouses, end_date)
    sales = generate_sales(rng, products, warehouses, end_date, history_days)
    purchase_orders = generate_purchase_orders(rng, products, suppliers, warehouses, end_date)

    datasets = {
        "products": products,
        "suppliers": suppliers,
        "warehouses": warehouses,
        "inventory": inventory,
        "sales": sales,
        "purchase_orders": purchase_orders,
    }

    validate_datasets(datasets)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in datasets.items():
        frame.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)

    print("\nDATA GENERATION SUCCESSFUL")
    for name, frame in datasets.items():
        print(f"{name:18} {len(frame):>7,} rows")
    print(f"\nFiles saved to: {OUTPUT_DIR}")
    return datasets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce inventory data.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()
    generate_all_datasets(seed=args.seed, history_days=args.days)
