# LitBridge — Hackathon 执行计划（重审版）

> 日期：2026-05-02
> 比赛：ANU AI Buildathon 2026.05（8h，剩余约 6.5h）
> 关联文档：`12-research-ai-literature-manager.md`（原始需求 brainstorm，仅供参考；技术选型以本文为准）

本文档是**从零审视后的最终方案**，不参考早期讨论。

---

## 一、产品

**一句话**：你的文献库 × 你的文章/Topic，AI 帮你连起来。

**两个功能**：
- **A. Smart Cite-Back**（亮点）：粘贴一篇正在写的文章 → 逐段给出 Top-3 引用建议
- **B. Topic Search**（兜底）：输入 Topic → 文献库内多文献摘要 + 原文片段

**每条结果必须带**：文件名 · 页码 · 原文片段 · 相关度。这是 AI 推荐可信度的命根子，砍什么都不能砍这个。

---

## 二、技术栈（最终决定）

| 层 | 选型 | 关键理由 |
|---|---|---|
| 前端 | **Streamlit** | Python 团队，单文件入口，最快交付 |
| 部署 | **Streamlit Community Cloud** | 免费、原生长连接、连 GitHub 一键部署，30 分钟拿到公网 URL |
| PDF 解析 | **PyMuPDF (`fitz`)** | 标准选择，不引入 unstructured |
| 分块 | **段落合并 400-700 tokens** + **截断 References 段** | 平衡语义完整与检索粒度；尾部截断防引用条目污染 |
| Embedding | **Voyage AI API**（`voyage-context-3`） | 专为 chunk-based RAG 优化，学术语义最优；省 700MB RAM；Streamlit Cloud 1GB 友好 |
| 向量库 | **ChromaDB 内存 client** | 5-10 PDF / 100-500 chunks 规模，零配置 |
| LLM | **Claude Haiku 4.5** 默认 + **Sonnet 4.6** 用于 Topic 总结 | Cite-Back 调用频次高用 Haiku；Topic 总结一次性输出长内容用 Sonnet |
| Prompt | 系统 prompt 走 **prompt caching**（`cache_control: ephemeral`） | 同 session 多次调用大幅省 token |

**与早期方案的关键差异**：
- ❌ ~~`sentence-transformers` 本地 embedding~~ → ✅ **Voyage `voyage-context-3`**（质量+RAM+冷启动三方面都赢）
- ❌ ~~Vercel 部署~~ → ✅ **Streamlit Community Cloud**（Streamlit 与 serverless 不兼容）
- ❌ ~~A/B 并行开发~~ → ✅ **B 先做（retrieve 最短闭环），A 后做**（A 多一步文章分段 + 多次 Claude + JSON）

`requirements.txt` 需要的最终依赖：
```
streamlit>=1.30
PyMuPDF>=1.23
chromadb>=0.4
anthropic>=0.40
voyageai>=0.2
python-dotenv>=1.0
```
（移除 `sentence-transformers`）

---

## 三、架构（扁平三文件）

```
app.py        # Streamlit UI + 路由 + Feature A/B 入口
rag.py        # PDF 解析 + 分块 + Voyage embed + Chroma + retrieve
llm.py        # Claude 封装（含 prompt caching、JSON 解析容错、retry）

data/
  pdfs/         # 5-10 篇 demo PDF（commit 进 repo）
  sample_draft.md
  index/        # 本地预生成的 embedding 缓存：chunks.json + embeddings.npy
                # 部署时 Cloud 只 load 不重 embed（见六、冷启动）
```

**单一原则**：A 和 B 都调用同一个 `rag.retrieve(query, k)`。Claude 只负责"总结"和"判断"，不负责检索。

不分 `embed.py` / `retrieve.py` / `ingest.py` / `cite_back.py` / `topic_search.py` —— 当前规模下分得越细切换成本越高。

---

## 四、时间线（6.5h）

| 时段 | 内容 | 验收 |
|---|---|---|
| **0:00 – 0:15** | **Smoke deploy**：最小 Streamlit 骨架（"Hello LitBridge"）+ Secrets 配好 + 部署 | 公网 URL 能打开。**15 分钟没通立刻切 HF Spaces 或本地 tunnel**，不要硬磕 |
| **0:15 – 1:30** | Ingest 管线：PDF → 段落分块（400-700 tokens） → 截断 References → Voyage embed → Chroma；同时**本地预生成 `data/index/` 缓存** | UI 显示「已加载 N 篇文献，M 个片段」，冷启动 < 5s |
| **1:30 – 3:00** | **Feature B**（先做，最短闭环）：topic 输入 → retrieve → Sonnet 总结 → 带原文片段 | 输入示例 topic 看到 3-5 条带文件名/页码/片段的结果 |
| **3:00 – 4:30** | **Feature A**：文章分段 → 每段 retrieve → Haiku 判断匹配 → 段落级 Top-3 展示 | 粘贴示例文章看到逐段建议，每段 3 条引用候选 |
| **4:30 – 5:30** | 兜底 + 抛光：JSON 解析容错、网络失败提示、限制输入长度/段落数、并发锁、sample 按钮 | 故意断网/超长输入不崩 |
| **5:30 – 6:30** | Pitch + demo 排练 + 备份录屏 | 4 分钟讲完不卡壳；URL 提前 warm up |

**4:30 强制功能冻结**：之后只动 UI 文案、文档、demo。

### Ingest 阶段的降级链（最容易滑坡的环节）

按出问题立即切：

1. **完整流程跑通** —— PyMuPDF 解析 + 段落分块 + 页码映射 + References 截断 + Voyage embed + Chroma
2. **降级 1：预抽文本 JSON** —— 解析卡壳就在本地手动跑通后存成 `data/index/chunks.json`，部署只 load
3. **降级 2：BM25 + Claude** —— Voyage / Chroma 出问题就用 `rank_bm25` 关键词检索 + Claude 总结，砍掉 embedding

---

## 五、部署清单（Streamlit Community Cloud）

1. GitHub repo（公开 / 已授权）
2. `app.py` 在根目录
3. `requirements.txt` 在根目录（更新如上）
4. `runtime.txt` 写 `python-3.11`
5. Streamlit Cloud Secrets 配 `ANTHROPIC_API_KEY` 和 `VOYAGE_API_KEY`，代码用 `st.secrets[...]` 读
6. demo PDF commit 进 `data/pdfs/`，部署时随代码带上（Streamlit Cloud 文件系统是临时的，但仓库内文件常在）
7. **本地预生成 embedding 缓存**：本地跑通 ingest 后将 chunks + embeddings 存到 `data/index/`（`chunks.json` + `embeddings.npy`），commit 进 repo。Cloud 启动只 load 不重 embed
8. App 启动时 `@st.cache_resource` 加载缓存，**冷启动 < 5s**（不是 30-60s）
9. **demo 前 5 分钟先打开 URL warm up**

资源限制：1GB RAM。Voyage API 几乎不占内存，PyMuPDF + ChromaDB + Streamlit ~ 200-300MB，余量充足。

线上评委场景的额外约束：
- **限制输入长度**：Topic 输入 ≤ 200 字符；Cite-Back 文章 ≤ 30 段或 5000 字
- **限制 Top-K**：Topic 总结 K=5；Cite-Back 每段 K=3
- **并发锁**：同一时间一个评委用，避免 token 飙升 / RAM 抖动
- **预置 sample 按钮**："试一下示例 topic" / "试一下示例文章"，降低评委摸索成本

备选（Streamlit Cloud 出问题时）：HuggingFace Spaces (Streamlit) / Cloudflare Tunnel + 本地。

---

## 六、必须解决的工程坑

按"最容易在最后 1h 爆"排序：

1. **References 段污染检索** — 论文末尾的引用条目分块后会被检索到当成"证据"。检测到关键词 `References` / `Bibliography` / `参考文献` 立即截断，或丢弃尾部 15% chunks
2. **Streamlit rerun 重复 ingest** — 任何交互都触发 rerun。`@st.cache_resource` 包索引 client 和 embedding model；`@st.cache_data` 包文件读取
3. **Claude JSON 解析失败** — 模型偶尔带说明文字。要求 JSON 输出 + 正则提取 `\{.*\}` + try/except 兜底返回空建议
4. **PDF 提取乱码** — 双栏 / 公式 / 扫描件可能给乱码。demo PDF **提前抽一遍验过**，肉眼检查文本质量
5. **API key 泄漏** — 永远走 `st.secrets`，不要 print，不要写 commit
6. **Voyage / Anthropic 限流** — Voyage embed 用 batch（一次塞多 chunks），Claude 调用加 retry

---

## 七、Demo 路径

```
1. 评委打开公网 URL
   首页：「LitBridge — 你的文献库 × 你的文章」+「已加载 N 篇文献」
2. 切到 Feature B：输入预设 topic（pitch 时讲清楚为什么选这个 topic）
   → 3-5 条结果，每条带文件名 · 页码 · 原文片段 · 相关度
3. 切到 Feature A：粘贴预置半成品文章
   → 段落级 Top-3 引用建议
4. 一句话收尾：「30 篇 PDF 不再是黑洞，AI 知道哪段配哪段」
```

**Pitch 钩子（候选）**：「为什么你看完 30 篇 PDF 还是不知道哪几段真有用？」

---

## 八、不做的事

- ❌ 单元测试 / mypy / lint
- ❌ 抽 BaseRetriever / Strategy 类
- ❌ LangChain / LlamaIndex
- ❌ section-aware 分块
- ❌ 用户系统、登录、多租户
- ❌ 一键插入 / 拖拽编辑器 / markdown 导出
- ❌ ChromaDB persistent / 外部向量库
- ❌ 写新文档（除非 demo 要展示）
- ❌ Vercel 部署（Streamlit 与 serverless 不兼容）
- ❌ 本地 sentence-transformers / SPECTER2
- ❌ Commit 付费 / 版权论文进 repo（公开 repo = 公开分发，违规）。**demo PDF 只用 arXiv / Open Access**

**必须保留**：每条推荐结果的 **文件名 + 页码 + 原文片段**。
