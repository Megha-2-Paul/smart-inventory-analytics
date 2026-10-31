"""Shared data access and presentation helpers for Streamlit pages."""
from __future__ import annotations

import streamlit as st

from src.data_cleaning import clean_datasets, load_datasets, validate_relationships
from src.inventory_metrics import build_inventory_position


@st.cache_data(show_spinner="Loading and validating inventory data...")
def get_data() -> dict:
    """Load, clean, validate and cache all generated datasets."""
    datasets = clean_datasets(load_datasets())
    validate_relationships(datasets)
    return datasets


def get_inventory_position(data: dict):
    return build_inventory_position(data["inventory"], data["products"])


def format_currency(value: float) -> str:
    return f"₹{value:,.0f}"
