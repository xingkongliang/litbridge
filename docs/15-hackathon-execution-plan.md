# LitBridge — Hackathon 执行计划与建议

> 日期：2026-05-02
> 比赛：ANU AI Buildathon 2026.05（8h，剩余约 6.5h）
> 关联文档：`12-research-ai-literature-manager.md`（需求与方案真源）

本文档是"执行视角"：在已有方案基础上，确定**做什么、不做什么、怎么排序、注意什么坑**。

---

## 一、产品目标（一句话）

**给一个文献库，一个目标（文章或 Topic），系统帮你找到最相关的内容并组织好。**

为谁解决：写论文/作业的学生，已经收了 20-30 篇 PDF，但不知道哪几篇真有用、哪段该引用。

---

## 二、产品需求（两个功能）

### Feature A — Smart Cite-Back（亮点）

用户上传一篇正在写的文章 + 一批 PDF 文献库。系统逐段分析文章，从文献库检索最相关的片段，**建议在文章具体位置插入引用**，用户确认。

差异化：市面上没有「自己的库 × 自己的文章 → 智能插入」这一档。Sourcely 偏本科水平，Elicit/Consensus 只搜外部库。

### Feature B — Topic Search（兜底）

用户输入一个研究 Topic 或问题，系统从文献库检索 + 阅读 + 总结出支持该论点的内容，附原文片段。

实现复杂度比 A 低很多，是经典 RAG。**作为 demo 兜底，必须先做出来。**

---

## 三、执行优先级（重要）

时间顺序 ≠ 重要顺序。按下面这条路径走，任何阶段被打断都还能 demo：

| 优先级 | 内容 | 不能跳的理由 |
|---|---|---|
| **P0** | 5-10 篇同领域 PDF + 一篇半成品文章（mock 数据） | 没有数据 demo 直接零分；可与编码并行做 |
| **P0** | PDF → chunks → ChromaDB 入库管线 | A 和 B 共用 |
| **P0** | Feature B（Topic 搜索 + 总结）端到端 | 兜底 demo，必须能跑 |
| **P1** | Feature A（段落级引用建议） | 差异化亮点；B 稳了再做 |
| **P1** | Pitch 一句话 + demo 脚本 | 评审看的是讲故事，不是代码 |
| **P2** | UI 美化、错误处理、边界情况 | 只在前面都跑通后做 |

**5h 时间点强制冻结**：如果 Feature A 还没跑通，停止开发，全力打磨 demo + 排练。

---

## 四、技术栈最终选型

| 层 | 选型 | 备注 |
|---|---|---|
| 前端 | Streamlit | `app.py` 单入口 |
| PDF 解析 | PyMuPDF (`fitz`) | 不引入 `unstructured`（依赖重） |
| 分块 | 固定 token + overlap（建议 500/100） | **不要按 section 分块**（见坑 #1） |
| Embedding | `sentence-transformers` 本地模型 `all-MiniLM-L6-v2` | 离线、免费、无配额；wifi 挂了也能 demo |
| 向量库 | ChromaDB persistent client（`./chroma_db/`） | |
| LLM | Anthropic Claude（`anthropic` SDK） | 默认 `claude-haiku-4-5-20251001`，关键总结用 `claude-sonnet-4-6` |

---

## 五、关键建议与坑（真实想法）

### 1. 不要按 section 分块

文档 12 建议按 Abstract/Method/Results 分块。**实际不可行**：PyMuPDF 拿不到稳定的 section 边界，正则覆盖不同论文格式至少烧 2 小时。固定 token + overlap 在 5-10 篇 demo 数据上效果不会明显差。

### 2. README 里的 embedding 名称是错的

README 写"Anthropic Voyage" — Voyage AI 是独立 SDK，且 `requirements.txt` 没装。直接用 `sentence-transformers`，hackathon 期间不要再换。

### 3. 不要碰 LangChain / LlamaIndex

看似省事，debug 内部行为比自己写两个函数还慢。直接 `chromadb.PersistentClient` + 一个 `retrieve(query, k)` 函数完事。

### 4. Streamlit 必须缓存重对象

ChromaDB client、embedding model 用 `@st.cache_resource` 包住，否则每次交互重载，demo 看着卡。

### 5. Claude 调用约定

- 系统 prompt 走 prompt caching（`cache_control: {"type": "ephemeral"}`）
- Cite-Back 的匹配判断要求 JSON 输出，不要解析自然语言
- 默认 Haiku，topic 总结这种长输出再上 Sonnet

### 6. Mock 数据是被低估的工作

5-10 篇 **同一细分领域**（NLP / 医疗 / 教育都行）的 PDF + 一篇带空缺的草稿文章。这个工作不写代码的人现在就该开始，**它决定 demo 的"哇"程度**。

### 7. Pitch 现在就定

候选钩子：「为什么你看完 30 篇 PDF 还不知道哪几篇真有用？」+「你的文献库，你的文章，AI 帮你把它们连起来」。让评审 5 秒内 get 到 pain point。

---

## 六、Demo 路径（评审看的就是这条路径）

```
1. 上传 5-10 篇 PDF（已预先准备）
2. 进度条显示 ingest（PyMuPDF + embedding + ChromaDB）
3. 选 Feature B：输入 topic → 显示 3-5 篇相关文献摘要 + 原文片段
4. 选 Feature A：粘贴半成品文章 → 段落高亮 + 右侧引用建议 + 一键插入
5. 导出带引用的 markdown
```

任何 PR / 改动先问：**这一步对 demo 路径有没有帮助？** 没有就先不做。

---

## 七、不做的事

- ❌ 单元测试
- ❌ 抽 BaseRetriever / Strategy 这种类
- ❌ LangChain / LlamaIndex
- ❌ section-aware 分块
- ❌ 用户系统、多租户、登录
- ❌ 写新的 .md 文档（除非 demo 要展示）
- ❌ OpenAI（已切到 Anthropic，commit `b7dbeb1`）
