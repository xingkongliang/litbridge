# AGENTS.md — LitBridge

ANU AI Buildathon 项目（8h 比赛）。学术 RAG 工具：用户文献库 × 用户文章/Topic → AI 匹配并组织。

需求与方案的真源：`docs/12-research-ai-literature-manager.md`。

## 决策原则

Hackathon 模式：**demo 跑通 > 完整正确**。遇到取舍来问我，别自己引入抽象、测试、文档、新依赖。

## 运行

```bash
conda run -n llm streamlit run app.py
```

`.env` 放 `ANTHROPIC_API_KEY`。

## 硬约束

- LLM 用 Anthropic Codex（`anthropic` SDK），不要用 OpenAI（已切换，commit `b7dbeb1`）
- 不引入 LangChain / LlamaIndex
- 不写单元测试、不新建 .md 文档（除非我明确要求）
