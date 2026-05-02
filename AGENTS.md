# AGENTS.md — LitBridge

ANU AI Buildathon project (8h hackathon). Academic RAG tool: user's literature library × user's draft / topic → AI matches and organizes.

Source of truth for requirements and design: `docs/12-research-ai-literature-manager.md`.

## Decision principles

Hackathon mode: **demo working > fully correct**. Surface tradeoffs to me — don't introduce abstractions, tests, documentation, or new dependencies on your own.

## Run

```bash
conda run -n llm streamlit run app.py
```

Put `ANTHROPIC_API_KEY` in `.env`.

## Hard constraints

- LLM uses Anthropic Codex (`anthropic` SDK); do not use OpenAI (already switched, commit `b7dbeb1`)
- Do not introduce LangChain / LlamaIndex
- Do not write unit tests or new `.md` docs (unless I explicitly ask)
