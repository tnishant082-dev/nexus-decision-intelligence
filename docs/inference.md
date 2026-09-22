# Inference architecture

LLM completions only. Statistical claims live in [`inferential-engineering.md`](./inferential-engineering.md).

Default path is a **CPU mock**. Labels `small` / `medium` / `large` are **slots**, not GPUs.

```
prompt → guardrails → queue(concurrency=1) → cache → route
       → mock | OpenAI-compatible HTTP
       → retry(2) → mock fallback
       → SQLite log (TTFT, tokens/s, cache, cost)
```

| Provider | Env | Status in this repo |
|---|---|---|
| mock / small / large | none | Live |
| OpenAI | `OPENAI_API_KEY` | HTTP adapter |
| Groq | `GROQ_API_KEY` | HTTP adapter |
| Ollama | `OLLAMA_BASE_URL` | HTTP adapter; process not started |
| vLLM | `VLLM_BASE_URL` | HTTP adapter; no GPU claimed |
| llama.cpp | `LLAMACPP_BASE_URL` | HTTP adapter |

TTFT is measured as time-to-HTTP-response (non-streaming). Cost is 0 unless `NEXUS_USD_PER_1K_IN/OUT` is set.

Router policy: short prompts → mock/small; domain analytics → medium slot (console) / small-medium (Python length heuristic); long/causal → large. Savings vs always-large are **relative mock timings** (85/180/420 ms, cost units 1/3/8).
