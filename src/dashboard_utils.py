"""Shared data access and presentation helpers for Streamlit pages."""
from __future__ import annotations

import streamlit as st

from src.data_cleaning import clean_datasets, load_datasets, validate_relationships
from src.data_generator import generate_all_datasets
from src.inventory_metrics import build_inventory_position


@st.cache_data(show_spinner="Loading and validating inventory data...")
def get_data() -> dict:
    """Load, clean, validate and cache datasets, generating demo data if absent."""
    try:
        raw_datasets = load_datasets()
    except FileNotFoundError:
        # Streamlit hosting environments may start with an empty data/raw folder.
        # Generate deterministic synthetic data on first launch.
        generate_all_datasets(seed=42, history_days=365)
        raw_datasets = load_datasets()

    datasets = clean_datasets(raw_datasets)
    validate_relationships(datasets)
    return datasets


def get_inventory_position(data: dict):
    return build_inventory_position(data["inventory"], data["products"])


def format_currency(value: float) -> str:
    return f"₹{value:,.0f}"
