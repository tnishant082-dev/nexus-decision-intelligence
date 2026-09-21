# Agent evaluation architecture

`evaluation/runner.py` runs six gold cases against snapshot-backed investigate/GraphRAG/RAG strings.

| Agent | Gold id | Must include |
|---|---|---|
| analytics | otif-late | otif, warehouse |
| forecast | forecast-rev | 2016, 2017 |
| inventory | inventory | stockout, coverage |
| risk | risk-late | late |
| rag | rag-otif | sample, otif |
| decision | decision | late, warehouse |

Tracked on each run: task success, tool list, latency, cost (0 on this path), hallucination (0 on snapshot strings), failure.

Hallucination rate is **0 because this path does not auto-judge live LLM completions**. Do not quote it as a model-quality result.

Guardrail probes (injection / PII / SQL write / clean OTIF) run alongside the gold set.
