# Smart Inventory & Stock Management Analytics

An end-to-end portfolio project demonstrating synthetic data generation, data quality checks, inventory analytics, demand forecasting, interactive Streamlit dashboards and downloadable business reports for a fictional e-commerce business.

> **Data notice:** All records are synthetic. They do not represent a real company, supplier, customer or transaction.

## Project configuration

- 500 products across multiple categories
- 50 suppliers
- 5 warehouses
- 2,500 product-warehouse inventory positions
- 12,000 sales transactions
- 1,000 purchase orders
- Configurable historical sales window (365 days by default)

## Technology

Python 3.10–3.12, Pandas, NumPy, Streamlit, Plotly, Scikit-learn, OpenPyXL, ReportLab and pytest.

## Quick start (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m src.data_generator
streamlit run app.py
```

For macOS/Linux, activate the environment with `source venv/bin/activate`.

## Generated datasets

The generator writes six CSV files to `data/raw/`:

| File | Description |
|---|---|
| products.csv | Product catalogue, category, pricing and supplier |
| suppliers.csv | Supplier profiles and lead times |
| warehouses.csv | Five warehouse locations and capacities |
| inventory.csv | Product stock by warehouse |
| sales.csv | Synthetic sales transactions |
| purchase_orders.csv | Purchase orders and delivery status |

Regenerate data with a fixed seed for reproducible random choices:

```bash
python -m src.data_generator --seed 42 --days 365
```

Calendar dates are relative to the run date, so they naturally shift when regenerated later.

## Dashboard pages

1. **Executive overview** — headline KPIs, inventory health, category revenue and priority reorder list.
2. **Inventory explorer** — search and filter products by category, warehouse and stock status.
3. **Stock alerts** — configurable demand lookback, safety stock and target stock cover.
4. **Demand forecasting** — moving-average baseline and Random Forest forecast comparison.
5. **Supplier analytics** — purchase value, delivery timing and supplier rating.
6. **Reports** — downloadable multi-sheet Excel workbook and PDF executive summary.

The app validates required columns and product, supplier and warehouse relationships before showing analytics. If the six CSV files are missing on first launch, the app generates the synthetic demo datasets automatically. You can also generate them manually with the command above.

## Run automated tests

```bash
pytest -q
```

GitHub Actions runs the test suite on pushes and pull requests to `main`, using Python 3.10, 3.11 and 3.12. Check the repository's **Actions** tab for the actual run result.

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub and ensure the default branch is `main`.
2. Open Streamlit Community Cloud and connect your GitHub account.
3. Create an app using this repository, branch `main` and main file path `app.py`.
4. Deploy the app. On first launch, the dashboard generates the six synthetic CSV files under `data/raw/` if they are not already present.
5. After deployment, open each page and verify the KPI values, filters, forecast charts and report downloads.

No API keys or secrets are required for the current synthetic-data version.

## Modelling and interpretation notes

- The initial stock snapshot and historical sales are generated independently. This version is intended for portfolio demonstration, not accounting-grade stock reconciliation.
- Forecasts are estimates based on synthetic history. Random Forest holdout MAE is a back-test metric, not a guarantee of future accuracy.
- Reorder suggestions are planning aids. Review supplier constraints, actual lead times and business context before placing orders.
- Supplier, sales, stock and financial values are fictional.
