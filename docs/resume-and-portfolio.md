## Technical achievements summary (v1.4)

Measurable, reproducible, not invented:

- Order-grain OTIF **40.83%** (Wilson 95% CI **40.46–41.21**, n=**65,752**, 26,849 successes) vs SAMPLE 92%.
- Extract revenue **$31.64M**; late-line exposure **$18.08M** (57.14% of sales) — exposure, not lost sales.
- GraphRAG snapshot **41 nodes / 112 edges**; Fan Shop **~$8.43M** late-line $ is the largest supplier node.
- Quality command **11/11** checks, score **100**, 0 incidents; lag vs today is informational.
- Gold eval **6/6** on snapshot-backed strings; hallucination **0** on that path; cost **$0**.
- Twin: inventory +20% → OTIF **42.43%**; lead time +5 days → OTIF **31.83%** (linear SAMPLE elasticities).
- Inference default **mock**; vLLM/Ollama/llama.cpp/OpenAI/Groq adapters idle unless env is set.

Commands: `python -m pytest tests/test_platform_v14.py tests/test_wilson.py`.
