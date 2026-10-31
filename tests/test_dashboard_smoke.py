"""Smoke-test every Streamlit page with generated synthetic demo data."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_FILES = [
    "app.py",
    "pages/1_Inventory_Explorer.py",
    "pages/2_Stock_Alerts.py",
    "pages/3_Demand_Forecasting.py",
    "pages/4_Supplier_Analytics.py",
    "pages/5_Reports.py",
]


@pytest.mark.parametrize("relative_path", DASHBOARD_FILES)
def test_dashboard_page_runs_without_exceptions(relative_path):
    app = AppTest.from_file(str(ROOT / relative_path), default_timeout=90).run()
    assert not app.exception, (
        f"{relative_path} raised Streamlit exceptions: "
        + "; ".join(str(item.message) for item in app.exception)
    )
