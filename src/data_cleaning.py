"""Load, clean, and validate the generated inventory CSV datasets."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

REQUIRED_COLUMNS = {
    "products": {"product_id", "sku", "product_name", "category", "supplier_id", "unit_cost", "selling_price", "reorder_level"},
    "suppliers": {"supplier_id", "supplier_name", "lead_time_days"},
    "warehouses": {"warehouse_id", "warehouse_name", "storage_capacity"},
    "inventory": {"product_id", "warehouse_id", "current_stock", "reserved_stock", "damaged_stock"},
    "sales": {"sales_id", "order_date", "product_id", "warehouse_id", "quantity", "revenue", "status"},
    "purchase_orders": {"purchase_order_id", "product_id", "supplier_id", "warehouse_id", "order_date", "quantity_ordered", "status"},
}


def load_datasets(data_dir: Path | str = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load all expected CSVs, raising a helpful error if one is missing."""
    folder = Path(data_dir)
    datasets = {}
    for name in REQUIRED_COLUMNS:
        path = folder / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run 'python -m src.data_generator' first."
            )
        datasets[name] = pd.read_csv(path)
    return datasets


def clean_datasets(datasets: Mapping[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Return cleaned copies; never mutate caller-owned frames."""
    cleaned = {name: frame.copy() for name, frame in datasets.items()}

    for name, required in REQUIRED_COLUMNS.items():
        if name not in cleaned:
            raise KeyError(f"Dataset '{name}' is missing.")
        missing_columns = required - set(cleaned[name].columns)
        if missing_columns:
            raise ValueError(f"{name} is missing required columns: {sorted(missing_columns)}")
        cleaned[name] = cleaned[name].drop_duplicates().reset_index(drop=True)

    date_columns = {
        "products": ["launch_date"],
        "inventory": ["last_restocked"],
        "sales": ["order_date"],
        "purchase_orders": ["order_date", "expected_delivery_date", "actual_delivery_date"],
    }
    for name, columns in date_columns.items():
        for column in columns:
            if column in cleaned[name]:
                cleaned[name][column] = pd.to_datetime(cleaned[name][column], errors="coerce")

    numeric_columns = {
        "products": ["unit_cost", "selling_price", "reorder_level", "lead_time_days"],
        "inventory": ["current_stock", "reserved_stock", "damaged_stock"],
        "sales": ["quantity", "unit_price", "unit_cost", "discount_pct", "revenue", "cost_of_goods"],
        "purchase_orders": ["quantity_ordered", "unit_cost", "total_cost"],
    }
    for name, columns in numeric_columns.items():
        for column in columns:
            if column in cleaned[name]:
                cleaned[name][column] = pd.to_numeric(cleaned[name][column], errors="coerce")

    # Remove unusable transaction rows, but preserve legitimate zero-stock rows.
    cleaned["sales"] = cleaned["sales"].dropna(
        subset=["sales_id", "order_date", "product_id", "warehouse_id", "quantity"]
    )
    cleaned["sales"] = cleaned["sales"].loc[cleaned["sales"]["quantity"] > 0].reset_index(drop=True)

    cleaned["inventory"] = cleaned["inventory"].dropna(
        subset=["product_id", "warehouse_id", "current_stock"]
    )
    for column in ["current_stock", "reserved_stock", "damaged_stock"]:
        cleaned["inventory"][column] = cleaned["inventory"][column].clip(lower=0)

    return cleaned


def validate_relationships(datasets: Mapping[str, pd.DataFrame]) -> None:
    """Raise ValueError when a foreign key points to a missing master record."""
    checks = [
        ("products", "supplier_id", "suppliers", "supplier_id"),
        ("inventory", "product_id", "products", "product_id"),
        ("inventory", "warehouse_id", "warehouses", "warehouse_id"),
        ("sales", "product_id", "products", "product_id"),
        ("sales", "warehouse_id", "warehouses", "warehouse_id"),
        ("purchase_orders", "product_id", "products", "product_id"),
        ("purchase_orders", "supplier_id", "suppliers", "supplier_id"),
        ("purchase_orders", "warehouse_id", "warehouses", "warehouse_id"),
    ]
    for child, child_col, parent, parent_col in checks:
        unknown = set(datasets[child][child_col].dropna()) - set(datasets[parent][parent_col].dropna())
        if unknown:
            raise ValueError(f"{child}.{child_col} contains unknown {parent} keys: {list(unknown)[:5]}")
