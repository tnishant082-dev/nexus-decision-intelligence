# Pull-request roadmap

Split before merging to `main` if you want reviewable diffs. All work currently lives on `platform-enterprise-upgrade`.

| PR | Title | Includes |
|---|---|---|
| 1 | Data contracts and warehouse views | `data-engineering/**`, metric dictionary, `tests/test_metrics.py` |
| 2 | Data science + ML comparison | `data-science/**`, `ml/**`, drift/tracking |
| 3 | RAG hybrid + investigate graph | `ai/**` |
| 4 | Inference gateway + API/security | `inference/**`, `backend/**`, observability |
| 5 | Streamlit console | `frontend/**` |
| 6 | Documentation + README | `docs/**`, `README.md` |

Do not merge README claims that CI has not run. After PR1, `python data-engineering/run_pipeline.py` must stay green.
