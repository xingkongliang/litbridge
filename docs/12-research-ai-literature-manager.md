# AI 文献管理工具 — 调研笔记

> 日期：2026-05-02
> 场景：ANU AI Buildathon 2026.05
> 核心需求：上传自己的文献库 → 智能匹配插入到文章中 / Topic → 文献总结

---

## 需求定义

### 功能一：文献 → 已有文章（智能插入引用）

用户有一篇正在写的文章，以及一批已收集的文献库（PDF）。系统分析文章每段内容，从文献库中检索最相关的文献片段，建议插入到文章的具体位置，用户选择确认。

### 功能二：文献 → 新 Topic（总结支撑）

用户输入一个研究 Topic 或问题，系统从已有文献库中检索、阅读、总结出支持该论点的内容和证据，帮助用户快速了解文献对该 Topic 的覆盖情况。

### 一句话概括

**给一个文献库，一个目标（文章或 Topic），系统帮你找到最相关的内容并组织好。**

---

## 一、竞品现状

| 工具 | 核心能力 | 差异点 |
|------|----------|--------|
| **Sourcely** | 自动找文献 + 插入引用 | 偏本科论文，深度不够 |
| **Elicit** | Topic → 文献检索 + 总结 | 强在搜索，不在你自己的文献库 |
| **Consensus** | Topic → 多文献证据聚合 | 只做搜索，不管理你已有的库 |
| **Scite** | 引用关系分析（支持/反对/提及） | 偏引用网络，不做写作辅助 |
| **Anara** | 上传 PDF → AI 分析 + 引用验证 | 最新，多媒体支持，但需付费 |
| **Zotero** | 经典文献管理 + 浏览器插件 | 无 AI 能力，靠插件生态 |

**切入点**：市面上缺一个「你上传自己的文献库 → 智能匹配插入到你的文章里」的工具。现有工具要么只做搜索（Elicit/Consensus），要么只做管理（Zotero），没有做 **自己的库 × 自己的文章 → 智能插入** 这个中间环节。

---

## 二、核心技术方案

### 整体架构

经典的 **RAG (Retrieval-Augmented Generation)**，针对学术场景定制。

### 推荐技术栈

- **前端**：Streamlit（最快出 demo，Python 全栈，hackathon 首选）
- **PDF 解析**：`PyMuPDF`（提取文本）+ `unstructured`（处理复杂布局/表格）
- **Embedding**：OpenAI `text-embedding-3-small`（便宜、效果好）或 `SPECTER2`（学术专用，免费的）
- **向量数据库**：ChromaDB 或 FAISS（本地零配置，hackathon 够用）
- **LLM**：GPT-4o-mini（便宜快，做匹配和总结够用）
- **分块策略**：学术论文建议按 section 分块（Abstract、Method、Results、Conclusion），比固定 token 分块语义更完整

### 两条管线

```
管线 A：文献库 → 向量索引（预计算，只做一次）
  PDF → 文本提取 → 按段落/section 分块 → Embedding → 存入 ChromaDB

管线 B：用户文章/Topic → 检索 + 生成
  文章分段 → 每段 Embedding → 从 ChromaDB 检索 Top-K 相关文献片段
  → LLM 判断匹配度 + 生成引用建议 → 展示给用户选择
```

---

## 三、参考开源项目

1. **kotaemon** (https://github.com/Cinnamon/kotaemon) — 开源 RAG 文档聊天工具，UI 好看，支持多用户、文件管理。可以 fork 来做前端基础，省大量时间。
2. **scientific-paper-chat-rag** (https://github.com/StadynR/scientific-paper-chat-rag) — 轻量级学术论文 RAG 聊天，代码简单易懂，适合参考架构。
3. **research-assistant-rag** (https://github.com/aragit/research-assistant-rag) — 全本地 RAG 研究助手，适合参考文献处理流程。

---

## 四、关键 API

- **Semantic Scholar API**（免费）：论文搜索、引用关系、推荐相似论文、获取 SPECTER2 embedding。不需要 API key 就能用（有 key 提升速率限制）。文档：https://api.semanticscholar.org/api-docs/
- **OpenAI API**：Embedding + GPT-4o-mini，核心都靠这个。

---

## 五、8 小时执行计划

| 阶段 | 时间 | 任务 |
|------|------|------|
| 0-1h | 搭建 | Streamlit 脚手架 + PDF 上传 + 基础 UI |
| 1-2.5h | 核心 A | PDF 解析 → 分块 → Embedding → ChromaDB 存储管线 |
| 2.5-4.5h | 核心 B | 文章/Topic 输入 → 检索 → 匹配度排序 → 引用建议展示 |
| 4.5-5.5h | 功能 B | Topic → 文献总结（第二个功能） |
| 5.5-6.5h | 打磨 | UI 美化 + mock 数据准备 + 错误处理 |
| 6.5-7.5h | 排练 | Demo 脚本 + Pitch 准备 |

**Mock 数据策略**：准备 5-10 篇同一领域的论文 PDF（如 NLP 或医疗），一篇半成品的文章，这样 demo 时路径最短、效果最明显。

---

## 六、Demo 亮点建议

1. **可视化匹配过程**：文章段落高亮 → 右侧展示匹配到的文献片段 + 相关度评分，用户点击插入
2. **对比效果**：展示「手动找引用 vs AI 推荐」的时间对比
3. **一句话 pitch**：「你的文献库，你的文章，AI 帮你把它们连起来」
