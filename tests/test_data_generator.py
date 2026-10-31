from src.data_generator import generate_all_datasets, validate_datasets


def test_generated_dataset_shapes_and_relationships():
    data = generate_all_datasets(seed=123, history_days=365)

    assert len(data["products"]) == 500
    assert len(data["suppliers"]) == 50
    assert len(data["warehouses"]) == 5
    assert len(data["inventory"]) == 500 * 5
    assert len(data["sales"]) == 12_000
    assert len(data["purchase_orders"]) == 1_000

    validate_datasets(data)


def test_inventory_has_one_record_per_product_warehouse():
    data = generate_all_datasets(seed=42, history_days=90)
    inventory = data["inventory"]

    assert not inventory.duplicated(
        ["product_id", "warehouse_id"]
    ).any()
