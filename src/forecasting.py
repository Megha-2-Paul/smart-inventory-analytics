"""Baseline and machine-learning demand forecasting utilities."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


def daily_product_demand(
    sales: pd.DataFrame,
    product_id: str,
    *,
    warehouse_id: str | None = None,
    end_date: str | pd.Timestamp | None = None,
    history_days: int = 180,
) -> pd.DataFrame:
    """Build a complete daily demand series, filling no-sale days with zero."""
    if history_days < 30:
        raise ValueError("history_days must be at least 30.")

    end = pd.Timestamp(end_date).normalize() if end_date is not None else pd.Timestamp.today().normalize()
    start = end - pd.Timedelta(days=history_days - 1)
    frame = sales.loc[
        sales["product_id"].eq(product_id)
        & sales["status"].eq("Completed")
    ].copy()
    if warehouse_id is not None:
        frame = frame.loc[frame["warehouse_id"].eq(warehouse_id)]

    frame["order_date"] = pd.to_datetime(frame["order_date"]).dt.normalize()
    frame = frame.loc[frame["order_date"].between(start, end)]
    daily = frame.groupby("order_date")["quantity"].sum()
    index = pd.date_range(start, end, freq="D")
    return daily.reindex(index, fill_value=0).rename("demand").rename_axis("date").reset_index()


def moving_average_forecast(
    daily_demand: pd.DataFrame,
    *,
    window: int = 7,
    horizon: int = 14,
) -> pd.DataFrame:
    """Recursive moving-average forecast for the requested future horizon."""
    if window < 1 or horizon < 1:
        raise ValueError("window and horizon must be positive.")
    values = daily_demand["demand"].astype(float).tolist()
    if not values:
        raise ValueError("daily_demand must contain at least one observation.")

    forecasts = []
    last_date = pd.to_datetime(daily_demand["date"]).max()
    history = values.copy()
    for step in range(1, horizon + 1):
        prediction = max(0.0, float(np.mean(history[-window:])))
        forecasts.append({"date": last_date + pd.Timedelta(days=step), "forecast_demand": prediction})
        history.append(prediction)
    return pd.DataFrame(forecasts)


def random_forest_forecast(
    daily_demand: pd.DataFrame,
    *,
    horizon: int = 14,
    lags: int = 14,
    random_state: int = 42,
) -> tuple[pd.DataFrame, float | None]:
    """Forecast daily demand with lag/calendar features.

    Returns (forecast_frame, holdout_MAE). The final 20% of historical
    observations are used as a chronological holdout where possible.
    """
    if horizon < 1 or lags < 2:
        raise ValueError("horizon must be positive and lags must be at least 2.")
    frame = daily_demand[["date", "demand"]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date").reset_index(drop=True)
    if len(frame) <= lags + 10:
        raise ValueError(f"At least {lags + 11} daily observations are required.")

    def make_features(data: pd.DataFrame) -> pd.DataFrame:
        result = pd.DataFrame(index=data.index)
        for lag in range(1, lags + 1):
            result[f"lag_{lag}"] = data["demand"].shift(lag)
        result["day_of_week"] = data["date"].dt.day_of_week
        result["day_of_month"] = data["date"].dt.day
        result["month"] = data["date"].dt.month
        result["is_weekend"] = (data["date"].dt.day_of_week >= 5).astype(int)
        return result

    features = make_features(frame)
    valid = features.notna().all(axis=1)
    X, y = features.loc[valid], frame.loc[valid, "demand"]
    split = max(int(len(X) * 0.8), 1)
    mae = None
    if len(X) - split >= 1 and split >= 10:
        evaluation_model = RandomForestRegressor(
            n_estimators=200, min_samples_leaf=2,
            random_state=random_state, n_jobs=-1
        )
        evaluation_model.fit(X.iloc[:split], y.iloc[:split])
        validation_predictions = evaluation_model.predict(X.iloc[split:])
        mae = float(mean_absolute_error(y.iloc[split:], validation_predictions))

    model = RandomForestRegressor(
        n_estimators=200, min_samples_leaf=2,
        random_state=random_state, n_jobs=-1
    )
    model.fit(X, y)

    history = frame[["date", "demand"]].copy()
    history["demand"] = history["demand"].astype(float)
    output = []
    for _ in range(horizon):
        next_date = history["date"].iloc[-1] + pd.Timedelta(days=1)
        row = {}
        for lag in range(1, lags + 1):
            row[f"lag_{lag}"] = float(history["demand"].iloc[-lag])
        row["day_of_week"] = next_date.day_of_week
        row["day_of_month"] = next_date.day
        row["month"] = next_date.month
        row["is_weekend"] = int(next_date.day_of_week >= 5)
        prediction = max(0.0, float(model.predict(pd.DataFrame([row]))[0]))
        output.append({"date": next_date, "forecast_demand": prediction})
        history.loc[len(history)] = [next_date, prediction]

    return pd.DataFrame(output), mae
