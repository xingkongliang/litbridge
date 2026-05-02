# LitBridge — Hackathon 执行计划

> 日期：2026-05-02 · ANU AI Buildathon（8h，剩约 6.5h）
> 关联：`12-research-ai-literature-manager.md`（原始 brainstorm，本文为准）

---

## 一、产品

**一句话**：你的文献库 × 你的文章/Topic，AI 帮你连起来。

- **A. Smart Cite-Back**（亮点）：粘贴文章 → 逐段 Top-3 引用建议
- **B. Topic Search**（兜底）：输入 Topic → 多文献摘要 + 原文片段

**每条结果必须带**：文件名 · 页码 · 原文片段 · 相关度。这是 AI 推荐可信度的命根子。

---

## 二、技术栈

| 层 | 选型 |
|---|---|
| 前端 | Streamlit |
| 部署 | Streamlit Community Cloud |
| PDF | PyMuPDF (`fitz`) |
| 分块 | 段落合并 400-700 tokens；检测 `References` / `Bibliography` 截断（极简版，不写复杂正则） |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2`（384-dim，本地）。**实测 Voyage 免费 tier 限速 3 RPM / 10K TPM**，demo 时每次查询要等 20s，不可用；切回本地完全消除限速 |
| 向量库 | ChromaDB 内存 client |
| LLM | Claude Haiku 4.5（统一一个模型，保留切 Sonnet 4.6 的常量备用） |

`requirements.txt`：`streamlit / PyMuPDF / chromadb / anthropic / voyageai / python-dotenv`

---

## 三、架构

```
app.py        # Streamlit UI + Feature A/B 入口
rag.py        # 解析 + 分块 + embed + Chroma + retrieve
llm.py        # Claude 封装 + JSON 解析容错

data/
  pdfs/         # 5-10 篇 demo PDF（arXiv / Open Access）
  sample_draft.md
  index/        # 本地预生成的 chunks.json + embeddings.npy（部署保险，见五）
```

A 和 B 共用同一个 `rag.retrieve(query, k)`。Claude 只负责总结和判断。

---

## 四、时间线（6.5h）

| 时段 | 内容 |
|---|---|
| **0:00 – 0:15** | Smoke deploy：最小骨架 + Secrets + 公网 URL。**15 分钟没通切 HF Spaces 或本地 tunnel** |
| **0:15 – 1:30** | rag.py：PDF → 分块 → Voyage embed → Chroma；本地预生成 `data/index/` 缓存 |
| **1:30 – 3:00** | **Feature B**（最短闭环）：topic → retrieve → Claude 总结 |
| **3:00 – 4:30** | **Feature A**：文章分段 → 每段 retrieve → Claude Top-3 判断 + JSON |
| **4:30 – 5:30** | 兜底 + 抛光：sample 按钮、输入长度限制、JSON 解析容错、网络失败提示 |
| **5:30 – 6:30** | Pitch + demo 排练 + 备份录屏 |

**4:30 强制功能冻结。**

### Ingest 出问题的降级链

1. 主路径失败 → 退到本地预生成 `chunks.json` + `embeddings.npy`，Cloud 只 load
2. 仍失败 → 砍 embedding，用 `rank_bm25` 关键词检索 + Claude 总结

---

## 五、部署清单（Streamlit Community Cloud）

1. GitHub repo 公开，`app.py` 在根目录
2. `requirements.txt` 在根目录，`runtime.txt` 写 `python-3.11`
3. Secrets 配 `ANTHROPIC_API_KEY` + `VOYAGE_API_KEY`，代码用 `st.secrets[...]` 读
4. demo PDF + 预生成 `data/index/` commit 进 repo（**部署保险**：Cloud 启动只 load，不重 embed，避免冷启动 API/网络失败）
5. `@st.cache_resource` 包 `load_index()`，避免 rerun 重载
6. **demo 前 5 分钟先打开 URL warm up**

资源：1GB RAM 够用（Voyage 走 API 不占内存）。

---

## 六、工程必修 checklist

写代码时一条都别漏：

- PDF 提取：demo PDF 提前肉眼检查文本质量（双栏 / 公式 / 扫描件易乱码）
- 分块：尾部检测 `References` / `Bibliography` / `参考文献` 关键字截断
- Streamlit：重对象用 `@st.cache_resource`，文件读用 `@st.cache_data`
- Claude：要求 JSON 输出 + 正则提取 `\{.*\}` + try/except 兜底
- Voyage：embed 用 batch；Anthropic 调用加 retry
- Secrets：永远走 `st.secrets`，不 print 不 commit

---

## 七、Demo 路径

```
1. 评委打开公网 URL，首页：「LitBridge」+「已加载 N 篇文献」+ sample 按钮
2. Feature B：点 sample topic → 3-5 条结果（文件名 · 页码 · 原文片段 · 相关度）
3. Feature A：点 sample 文章 → 段落级 Top-3 引用建议
4. 收尾一句话
```

提前定好，避免最后 30 分钟乱。

---

## 八、不做的事

- ❌ 单元测试 / 抽象层 / LangChain
- ❌ Vercel 部署（与 Streamlit 长连接不兼容）
- ❌ 本地 sentence-transformers（Voyage 质量更优 + 省 RAM）
- ❌ section-aware 分块 / 复杂 References 正则
- ❌ 一键插入 / 拖拽编辑器 / markdown 导出
- ❌ Commit 付费 / 版权论文（公开 repo = 公开分发）
- ❌ prompt caching / 双模型分级（hackathon 收益 < 调试成本）

**必须保留**：每条推荐结果的 **文件名 + 页码 + 原文片段**。
