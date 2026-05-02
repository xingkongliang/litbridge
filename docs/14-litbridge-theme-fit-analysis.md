# LitBridge × Theme Brief 对照分析

> 日期：2026-05-02
> 背景：ANU AI Buildathon — Theme: Tool for Students

---

## 核心挑战对照

| 要求 | LitBridge |
|------|-----------|
| 帮学生解决**真实**学术问题 | ✅ 写论文找引用是每个研究生的真实痛点 |
| 不是通用 chatbot | ✅ 有明确的两条工作流（文章补引用 / Topic 查文献） |
| 有清晰的 workflow | ✅ 上传 PDF → 系统索引 → 输入文章/Topic → 获取推荐 |
| 可演示的价值 | ✅ 90 秒内能看到从文章到引用推荐的全过程 |

---

## Focus Area 匹配分析

**目标方向：The Struggling Learner** — 帮学生理解困难的课程内容。

| 期望 | LitBridge | 匹配 |
|------|-----------|------|
| 诊断学生不理解什么 | LitBridge 不诊断"学生哪里不懂"，而是帮找文献支撑 | ⚠️ 偏弱 |
| 用例子/步骤/类比解释概念 | 不做。LitBridge 不解释概念本身 | ❌ |
| 包含练习题、反馈 | 不做 | ❌ |
| 引导主动学习，不给直接答案 | 推荐引用让学生自己去读原文，不是直接写好段落 | ✅ |

### 风险点

LitBridge 的核心是「文献匹配 + 引用推荐」，这更像是一个 productivity 工具（Overwhelmed Student 方向），但又不完全匹配 Overwhelmed Student 的「截止日期/任务管理」场景。

评委可能质疑：**"这帮的是写论文的人，不是一个在挣扎学习的学生。"**

---

## 调整方案

### 方案 A：微调定位，强行贴合 Struggling Learner

把功能包装成「阅读理解助手」：
- 上传一批论文 PDF（阅读材料）
- 学生输入"我不理解 Transformer 的 attention 机制"
- 系统从论文库中找到相关段落，**总结解释**，并标注出处
- 变成：**"帮学生在大量阅读材料中找到并理解相关内容"**

### 方案 B：转投 The Overwhelmed Student

重新定义痛点：
- "研究生被 30 篇论文淹没，不知道哪篇和自己的研究相关"
- LitBridge = 文献过滤器 + 优先级排序
- 更自然，但也不是完美匹配

### 方案 C（推荐）：双面包装

产品名叫 LitBridge，核心不变，但 pitch 时说：

> "The Struggling Learner who is drowning in reading lists and doesn't know which papers actually matter for their assignment."

把「找引用」包装成「从 30 篇论文中找到你最需要读的那 3 篇」，重点放在 **"帮你读对东西"** 而不是 "帮你写引用"。Demo 时先展示 Topic → 找到最相关文献（学习导向），再展示文章 → 推荐插入（写作导向）。

---

## 评分总结

| 维度          | 评分     | 说明                         |
| ----------- | ------ | -------------------------- |
| 主题匹配        | ⚠️ 3/5 | 功能上偏 productivity，需要重新包装叙事 |
| 不是 chatbot  | ✅ 5/5  | 完全不是                       |
| 清晰 workflow | ✅ 5/5  | 输入→处理→输出很清晰                |
| 90s 可演示     | ✅ 4/5  | 需要准备好 mock 数据              |
| AI 必要性      | ✅ 5/5  | 语义匹配和总结必须 AI               |
| 8h 可行       | ✅ 4/5  | RAG 管线成熟，Streamlit 快速出 UI  |
|             |        |                            |

### 关键结论

别把 LitBridge 定位成「引用管理工具」，定位成 **"帮学生在海量文献中找到真正需要读的那几篇"**。评委买的是"帮挣扎的学生"这个故事，不是"帮写论文的人省时间"。
