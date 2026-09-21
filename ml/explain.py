"""Feature importance + optional SHAP (never faked)."""
from __future__ import annotations

from typing import Any

import numpy as np


def tree_importance(model, feature_names: list[str]) -> list[dict[str, Any]]:
    names = list(feature_names)
    if hasattr(model, "feature_importances_"):
        vals = np.asarray(model.feature_importances_, dtype=float)
        return [{"feature": n, "importance": float(v)} for n, v in zip(names, vals)]
    return []


def shap_values(model, X, feature_names: list[str], max_rows: int = 200) -> dict[str, Any]:
    try:
        import shap  # type: ignore
    except Exception:
        return {"available": False, "reason": "shap package not installed"}
    sample = X.iloc[:max_rows] if hasattr(X, "iloc") else X[:max_rows]
    try:
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(sample)
        if isinstance(values, list):
            values = values[1] if len(values) > 1 else values[0]
        mean_abs = np.abs(np.asarray(values)).mean(axis=0)
        return {
            "available": True,
            "mean_abs_shap": [
                {"feature": n, "mean_abs_shap": float(v)} for n, v in zip(feature_names, mean_abs)
            ],
            "rows_explained": int(len(sample)),
        }
    except Exception as e:
        return {"available": False, "reason": str(e)}
