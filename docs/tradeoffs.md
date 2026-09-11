# Design Tradeoffs

| Choice | Why | Tradeoff |
|---|---|---|
| DuckDB file warehouse | Zero-ops local analytics, fast parquet scan | Not a multi-writer production warehouse |
| Mock LLM default | Works offline, honest demos | No free-form reasoning without a provider key |
| Lexical RAG | No embedding model download | Weaker semantic recall than dense vectors |
| HistGradientBoosting forecast | Strong baseline, no native xgboost dep | Not SOTA deep forecasting |
| Churn label = 180d recency | Uses real customer extract | Label leakage if recency kept as feature — registry uses leakage-aware model |
| Keep Power BI + Streamlit | Extend existing BI asset | Two UI surfaces to maintain |
| IsolationForest anomalies | Simple unsupervised OTIF/late flags | Contamination hyperparameter is heuristic |
