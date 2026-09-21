"""Optional boosting/prophet adapters — sklearn is the verified default."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier


def available_regressors() -> dict[str, Any]:
    models: dict[str, Any] = {
        "sklearn_hist_gbr": HistGradientBoostingRegressor(
            max_depth=4, learning_rate=0.08, max_iter=120, random_state=42
        ),
    }
    try:
        import xgboost as xgb  # type: ignore

        models["xgboost"] = xgb.XGBRegressor(
            n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42, n_jobs=1
        )
    except Exception:
        pass
    try:
        import lightgbm as lgb  # type: ignore

        models["lightgbm"] = lgb.LGBMRegressor(
            n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42, verbose=-1
        )
    except Exception:
        pass
    return models


def available_classifiers() -> dict[str, Any]:
    models: dict[str, Any] = {
        "sklearn_hist_gbc": HistGradientBoostingClassifier(max_depth=3, max_iter=80, random_state=42),
    }
    try:
        import xgboost as xgb  # type: ignore

        models["xgboost"] = xgb.XGBClassifier(
            n_estimators=80, max_depth=3, learning_rate=0.08, random_state=42, n_jobs=1, eval_metric="logloss"
        )
    except Exception:
        pass
    try:
        import lightgbm as lgb  # type: ignore

        models["lightgbm"] = lgb.LGBMClassifier(
            n_estimators=80, max_depth=3, learning_rate=0.08, random_state=42, verbose=-1
        )
    except Exception:
        pass
    return models


def prophet_forecast(train_df, horizon_index) -> np.ndarray | None:
    """Return None unless prophet is installed. Does not invent accuracy."""
    try:
        from prophet import Prophet  # type: ignore
    except Exception:
        return None
    if "ds" not in train_df.columns or "y" not in train_df.columns:
        return None
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m.fit(train_df[["ds", "y"]])
    future = horizon_index.rename(columns={"week_start": "ds"}) if "week_start" in horizon_index.columns else horizon_index
    fcst = m.predict(future)
    return fcst["yhat"].to_numpy()
