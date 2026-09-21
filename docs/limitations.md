# Limitations (read before quoting NEXUS)

- **Not hosted SaaS.** Local-first portfolio platform.
- **Late-line $ is exposure, not lost sales** and not recovered EBITDA.
- **SAMPLE policies** in `docs/knowledge/` are RAG fixtures, not live SOPs.
- **Customer names are not used** in GraphRAG; nodes are segments.
- **GraphRAG is a snapshot** (41/112). Neo4j is idle unless you run it.
- **Twin is linear SAMPLE elasticities**, not OMS/WMS physics.
- **LLM default is mock.** vLLM / Ollama / llama.cpp / OpenAI / Groq are HTTP adapters; this repo does not start those servers or claim GPUs.
- **Eval hallucination = 0** only on snapshot-backed strings. Live Grok/OpenAI answers are not auto-scored.
- **Streaming is weekly replay** of the extract. Kafka/Redpanda stay idle without a broker.
- **Memory is a JSON file / browser localStorage**, not a hosted incident store.
- **Auth is a shared API key** in the Python API. The App Builder console is auth-off.
- **Inventory on-hand $ summed over snapshots is not a balance sheet.**
- **2018 is a partial month** and is excluded from the 2016→2017 YoY pair.
