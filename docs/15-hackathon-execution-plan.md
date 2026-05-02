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

用户上传一篇正在写的文章 + 一批 PDF 文献库。系统逐段分析文章，对每段给出 **Top-3 引用建议**（带原文片段、文件名、页码、相关度）。

**砍掉的复杂交互**：一键插入 / 右侧拖拽 / markdown 导出。亮点靠**匹配效果**，不靠 UI。评审看的是"AI 真的找对了相关文献"，不是"插入按钮好不好用"。

差异化：市面上没有「自己的库 × 自己的文章 → 智能匹配」这一档。Sourcely 偏本科水平，Elicit/Consensus 只搜外部库。

### Feature B — Topic Search（兜底）

用户输入一个研究 Topic 或问题，系统从文献库检索 + 阅读 + 总结出支持该论点的内容，附原文片段。

实现复杂度比 A 低很多，是经典 RAG。**作为 demo 兜底，必须先做出来。**

---

## 三、执行优先级（重要）

时间顺序 ≠ 重要顺序。按下面这条路径走，任何阶段被打断都还能 demo：

| 优先级 | 内容 | 不能跳的理由 |
|---|---|---|
| **P0（前 30 分钟）** | Streamlit 单页骨架 + mock 结果展示 | 不先有 app.py，后面全是空中楼阁 |
| **P0** | 5-10 篇同领域 PDF + 一篇半成品文章（mock 数据） | 没有数据 demo 直接零分；可与编码并行做 |
| **P0** | PDF → chunks → 向量检索 入库管线（先内存索引） | A 和 B 共用 |
| **P0** | Feature B（Topic 搜索 + 总结）端到端 | 兜底 demo，必须能跑 |
| **P0** | Feature A（逐段 Top-3 引用建议，**纯展示，不做插入交互**） | 亮点；B 跑通后并行做，不要等 B 打磨完 |
| **P1** | Pitch 一句话 + demo 脚本 + 预置索引 | 评审看的是讲故事，不是代码 |
| **P2** | UI 美化、错误处理、边界情况 | 只在前面都跑通后做 |

**4.5h 时间点强制功能冻结**（不是 5h）：剩下 2h 全部用于 demo 数据预置、缓存、排练、兜底截图。Hackathon 输在最后 1h 还在改 bug。

---

## 四、技术栈最终选型

| 层 | 选型 | 备注 |
|---|---|---|
| 前端 | Streamlit | `app.py` 单入口 |
| PDF 解析 | PyMuPDF (`fitz`) | 不引入 `unstructured`（依赖重） |
| 分块 | **段落合并到 400-700 tokens** | 不要按 section 分块（见坑 #1）；500/100 固定切会把引用证据切碎 |
| Embedding | `sentence-transformers` 本地模型 `all-MiniLM-L6-v2` | 离线、免费、无配额；**模型必须提前下载并 warm up**，现场首次下载会卡死 |
| 向量库 | ChromaDB **内存 client**（`chromadb.Client()`） | hackathon 不需要 persistent；跑稳了再说 |
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

### 8. 比算法更容易炸的工程坑

这些不解决，最后 1h 必爆：

- **PDF 提取乱码** — 双栏 / 公式 / 扫描件 PyMuPDF 可能给一堆 ligature 乱码。demo PDF 必须**提前抽一遍验过**。
- **参考文献段污染检索** — 论文末尾的 References 章节会被分块进库，检索时返回一堆引用条目当成证据。**必须截断**（关键词 "References" / "Bibliography" 截断，或丢弃尾部 15%）。
- **Streamlit rerun 重复 ingest** — 上传文件后任何交互都会触发 rerun，没缓存就反复处理 PDF。`@st.cache_resource` 包索引、`@st.cache_data` 包 ingest 函数。
- **Claude JSON 解析失败** — 模型偶尔会返回带前后说明的 JSON。用 `response_format` 或正则提取 `\{.*\}`，**必须 try/except 兜底**。
- **API key / 网络** — 比赛场地 wifi 不稳是常态。embedding 已用本地模型，Claude 这一路要有"网络失败时显示缓存示例"的兜底。

### 9. 现场 ingest 不能让评审等

Demo 时**绝对不要**让评审看着 ingest 5-10 篇 PDF 的进度条转 1 分钟。预置索引（程序启动时自动加载 `data/pdfs/` 下所有文件并入库），demo 流程里 PDF 上传只是"装样子"。

---

## 六、Demo 路径（评审看的就是这条路径）

```
1. 启动时索引已预置好，UI 显示「已加载 N 篇文献」
   （上传按钮可以露出，但 demo 不实际触发现场 ingest）
2. 选 Feature B：输入 topic → 显示 3-5 篇相关文献摘要
   每条必须带：文件名 · 页码 · 原文片段 · 相关度
3. 选 Feature A：粘贴半成品文章 → 段落级 Top-3 引用建议
   每条同样带：文件名 · 页码 · 原文片段 · 相关度
4. 一句话总结："你的文献库 × 你的文章，AI 帮你连起来"
```

**可信度三件套**（文件名 / 页码 / 原文片段）必须出现在每个推荐结果里，否则评审默认你在编。

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
- ❌ 一键插入 / 拖拽 / markdown 导出（A 只展示推荐，不做编辑器交互）
- ❌ ChromaDB persistent 存储（先内存）

**必须保留**（不能砍）：每条推荐结果的 **文件名 + 页码 + 原文片段**——这是 AI 推荐可信度的命根子。
