"""Exercise key dashboard controls beyond page-load smoke tests."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def run_page(path: str):
    return AppTest.from_file(str(ROOT / path), default_timeout=120).run()


def test_inventory_category_filter_updates_results():
    app = run_page("pages/1_Inventory_Explorer.py")
    assert not app.exception
    category_filter = app.selectbox[0]
    category = next(option for option in category_filter.options if option != "All")
    category_filter.select(category).run()
    assert not app.exception
    assert app.metric[0].label == "Stock positions"


def test_stock_alert_assumptions_can_be_changed():
    app = run_page("pages/2_Stock_Alerts.py")
    assert not app.exception
    app.slider[0].set_value(45).run()
    assert not app.exception
    assert app.metric[0].label == "Critical stockouts"


def test_reports_page_exposes_both_downloads():
    app = run_page("pages/5_Reports.py")
    assert not app.exception
    labels = [item.label for item in app.get("download_button")]
    assert "Download Excel report" in labels
    assert "Download PDF report" in labels
