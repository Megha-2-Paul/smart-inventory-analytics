import pandas as pd
import pytest

from src.data_cleaning import clean_datasets, validate_relationships
from src.data_generator import generate_all_datasets


def test_cleaning_removes_duplicate_rows_and_preserves_dataset_keys():
    raw = generate_all_datasets(seed=17, history_days=60)
    raw["sales"] = pd.concat([raw["sales"], raw["sales"].iloc[[0]]], ignore_index=True)

    cleaned = clean_datasets(raw)

    assert len(cleaned["sales"]) == len(raw["sales"]) - 1
    validate_relationships(cleaned)


def test_cleaning_rejects_missing_required_columns():
    raw = generate_all_datasets(seed=18, history_days=30)
    raw["products"] = raw["products"].drop(columns=["sku"])

    with pytest.raises(ValueError, match="sku"):
        clean_datasets(raw)


def test_relationship_validation_rejects_unknown_product_key():
    raw = generate_all_datasets(seed=19, history_days=30)
    raw["inventory"].loc[0, "product_id"] = "UNKNOWN_PRODUCT"

    with pytest.raises(ValueError, match="unknown products keys"):
        validate_relationships(raw)
