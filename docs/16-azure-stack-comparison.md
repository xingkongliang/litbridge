# 技术栈对比：当前方案 vs Azure 全栈

> 日期：2026-05-02
> 上下文：LitBridge hackathon，剩 6.5h；评估是否将 PDF 解析与向量库切换到 Azure 服务
> 关联：`15-hackathon-execution-plan.md`（最终方案）

---

## 一、PDF 解析对比

| 维度 | PyMuPDF（当前） | Azure Document Intelligence |
|---|---|---|
| 安装 / 配置 | `pip install` 完事 | Azure 账户 + 资源 provision + API key + SDK，**~30-60 分钟** |
| 干净 arXiv PDF | 95% 没问题 | 一样好 |
| 复杂表格 / 公式 | 拿不到结构 | **明显更强**（layout model 返回结构化 JSON） |
| 扫描件 / OCR | ❌ 完全不行 | ✅ 内置 OCR |
| 多栏布局 | 文本顺序可能乱 | 自动按阅读顺序还原 |
| 解析延迟 | <100ms / PDF（本地） | **5-15s / PDF**（网络往返） |
| 故障点 | 仅本地代码 | API / 网络 / 限流 / 鉴权（4 个） |
| 免费额度 | 无限 | 500 页/月 F0 tier（hackathon 够用） |

---

## 二、向量数据库对比

| 维度 | ChromaDB 内存（当前） | Azure AI Search |
|---|---|---|
| 安装 / 配置 | 零配置 | 资源 provision + 索引 schema + 向量字段 + indexer，**~30-60 分钟** |
| 5-10 PDF / 100-500 chunks 性能 | 微秒级 cosine | 一样快，但多一次网络往返 |
| 持久化 | 无（要 commit `data/index/`） | ✅ 自带 |
| 混合检索（向量 + 关键词） | 要自己实现 | ✅ 内置 |
| 语义重排（semantic ranker） | 无 | ✅ 但**仅 Basic 套餐及以上**（~$75/月起） |
| 免费额度 | 无限本地 | F1 tier：50MB 存储 / 3 索引 / 无 semantic ranker |
| 故障点 | 仅本地 | API / 索引同步 / 网络（3 个） |

---

## 三、综合成本

| 指标 | 当前方案 | Azure 全栈 |
|---|---|---|
| 总设置时间 | 0（已就绪） | **~2h（剩余时间的 31%）** |
| 网络故障点 | 1 | **7**（DI 4 + Search 3） |
| 现场 wifi 不稳风险 | 仅影响评委访问 | 影响每次 PDF 解析 + 检索 |
| Demo 质量提升（5 篇 arXiv 尺度） | — | 评委肉眼分不出 |

---

## 四、决策矩阵

| 场景 | 建议 |
|---|---|
| **没有 Azure 赞助加分**（无 "Best Use of Azure" 奖项） | 维持 PyMuPDF + ChromaDB。Azure 是"以正确的方式做错误的事" |
| **有 Azure 加分** | **混合方案**：Document Intelligence 做解析（真有质量价值）+ 仍用 ChromaDB 内存（AI Search 设置成本不值） |
| **demo PDF 包含扫描件 / 复杂表格 / 公式** | 即使没 Azure 加分，**只换 Document Intelligence**，AI Search 不换 |

---

## 五、决定 Azure 价值的两个变量

切换前必须先回答：

1. **ANU AI Buildathon 有没有 Azure / Microsoft 赞助商加分？**
   - 如果有 "Best Use of Azure" 奖项或 Azure 是主赞助商，加分本身就是产品价值，成本计算反转
2. **demo PDF 是什么质量？**
   - 全 LaTeX 干净 arXiv → PyMuPDF 完全够
   - 包含扫描件 / 复杂表格 / 多栏 / 公式 → Document Intelligence 真有价值

这两个变量决定一切。在不知道答案前不要切换。

---

## 六、结论

**默认维持当前方案**（PyMuPDF + ChromaDB 内存）。

只有在**赞助商加分明确存在**或 **demo PDF 质量复杂**时才考虑切。即使切，也只切 Document Intelligence，AI Search 在 hackathon 尺度永远不值得。

Hackathon 评委不看技术栈品牌，只看 demo 出彩程度。每多 1h 设置就是少 1h 打磨亮点。
