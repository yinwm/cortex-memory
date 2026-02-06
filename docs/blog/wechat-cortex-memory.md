# 我做了一个 AI 记忆系统：让 AI 像人一样拥有长期记忆

> 开源项目：Cortex Memory - https://github.com/yinwm/cortex-memory

## 为什么要做这个？

你有没有遇到过这样的困扰：

- 💬 和 Claude 聊了一个小时，重启对话后它就"失忆"了
- 📝 昨天的灵感记在笔记里，今天想找却翻了半天
- 🤖 想做一个 AI Agent，但它没法记住之前学到的东西

**问题的本质：AI 没有"长期记忆"。**

Claude、ChatGPT 这些 LLM 只有"短期记忆"（上下文窗口），对话结束后就忘了一切。而人类的智能很大程度上依赖于**长期记忆** —— 我们会记住重要的经验、知识、决策，并在需要时调取。

**所以我做了 Cortex Memory：一个给 AI（和你自己）的长期记忆系统。**

---

## 它长什么样？

### 使用场景 1：个人知识管理

你在用 Claude Code 开发时遇到了一个坑：

```markdown
## 14:30 - knowledge
macOS 系统自带 Python 不支持 SQLite 扩展加载，
需要用 pysqlite3 替代系统 sqlite3 模块

**Tags**: #sqlite #database #macos #troubleshooting
**Importance**: 0.8
```

保存到 `~/.my-memory/2026-02/2026-02-05.md`，然后运行：

```bash
python3 scripts/summarize_day.py --date 2026-02-05
```

Cortex 会：
1. 用 Claude 提取这条记忆的核心价值
2. 用 bge-m3 模型生成 1024 维向量
3. 存入 SQLite 数据库 + 向量索引

**一周后**，你又遇到类似问题，搜索：

```bash
python3 scripts/retrieve_memory.py --query "sqlite 兼容性"
```

**立刻找到这条记忆**，不用再踩同样的坑。

---

### 使用场景 2：AI Agent 的长期记忆

你在做一个多 Agent 系统，希望 Agent 之间能共享知识：

```python
def agent_think(user_input):
    # 1. 检索相关记忆
    memories = retrieve_memories(user_input, limit=5)

    # 2. 用记忆作为上下文
    context = "\n".join([m["summary"] for m in memories])

    # 3. 调用 LLM
    response = call_llm(f"Context: {context}\n\nUser: {user_input}")

    # 4. 保存新的见解
    extract_memory(response)

    return response
```

**Agent A** 学到的东西，**Agent B** 也能用 —— 这就是共享的"长期记忆"。

---

## 技术设计：三层架构

### 第一层：Daily Files（日常笔记）

```
~/.my-memory/
  2026-02/
    2026-02-05.md
    2026-02-04.md
```

这是最简单的层级：**纯 Markdown 文件**，人类可读，Git 友好。

格式很简单：

```markdown
## 14:30 - knowledge
这是一条知识点

**Tags**: #tag1 #tag2
**Importance**: 0.8
```

类型可以是：
- `task` ✅ 任务和行动项
- `knowledge` 💡 重要知识点
- `note` 📝 普通笔记
- `noise` 💭 临时想法（不会被提取到长期记忆）

---

### 第二层：Summarization（智能提取）

每天结束时，运行 `summarize_day.py`：

```python
# 1. 读取今天的 markdown 文件
entries = read_memory_entries("2026-02-05.md")

# 2. 调用 Claude 提取长期记忆
summaries = summarize_with_claude(entries)
# Claude 会判断：哪些值得长期保存？哪些只是临时噪音？

# 3. 生成向量 embedding
for summary in summaries:
    embedding = get_embedding(summary)  # 调用 Ollama bge-m3
    save_to_db(summary, embedding)
```

**关键设计：用 Claude 做"记忆筛选"**

为什么不直接把所有笔记都存数据库？因为：
- ❌ 大量噪音会污染检索结果
- ❌ 向量生成有成本（时间 + 计算）
- ✅ Claude 能理解"什么值得长期记住"

这就像人脑的**记忆巩固**过程 —— 睡觉时，大脑会把重要的短期记忆转化为长期记忆。

---

### 第三层：Vector Database（语义检索）

数据库设计：

```sql
-- 记忆表（UUID 主键，支持多设备合并）
CREATE TABLE memories (
    uuid TEXT PRIMARY KEY,
    date TEXT,
    summary TEXT,
    importance REAL,
    metadata TEXT
);

-- 向量表（sqlite-vec）
CREATE VIRTUAL TABLE vec_memories USING vec0(
    embedding float[1024]
);

-- 映射表（向量 rowid <-> 记忆 UUID）
CREATE TABLE vec_memory_mapping (
    vec_rowid INTEGER,
    memory_uuid TEXT
);
```

**为什么用 UUID 而不是自增 ID？**

因为我想支持**多设备同步**：
- 设备 A 创建记忆 `uuid-123`
- 设备 B 创建记忆 `uuid-456`
- Git 合并时不会冲突（UUID 全局唯一）

---

## 检索算法：混合搜索

**单纯的向量搜索不够好**，我设计了混合算法：

```python
def retrieve_memories(query, limit=10):
    # 1. 语义搜索（70%）
    semantic_results = vector_search(query, limit=10)

    # 2. 关键词搜索（30%）- 最近 3 天的文件
    keyword_results = grep_recent_files(query, days=3)

    # 3. 合并 + 加权
    final_results = merge_results(
        semantic_results,
        keyword_results,
        semantic_weight=0.7
    )

    return final_results[:limit]
```

**为什么要混合？**

| 场景 | 纯向量搜索 | 混合搜索 |
|------|-----------|---------|
| 搜索 "sqlite-vec" | 可能找到 "数据库优化" | ✅ 精确匹配 |
| 搜索 "数据库问题" | ✅ 语义相关 | ✅ 更全面 |
| 最近 1-2 天的记忆 | 可能没入库 | ✅ 关键词补充 |

**关键词搜索**保证了：
- ✅ 精确匹配（专有名词、代码片段）
- ✅ 实时性（最近 3 天的笔记可能还没 summarize）

---

## 技术栈选择

### 为什么用 SQLite？

很多人第一反应是用 Pinecone、Qdrant 这些专业向量数据库。但我选择 SQLite：

**优点：**
- ✅ 单文件，零运维
- ✅ 本地存储，隐私安全
- ✅ Git 友好，多设备同步简单
- ✅ [sqlite-vec](https://github.com/asg017/sqlite-vec) 性能足够好（百万级别）

**缺点：**
- ❌ 不适合超大规模（千万级）
- ❌ 没有分布式

但对于**个人记忆系统**来说，一年也就几千条记忆，SQLite 完全够用。

---

### 为什么用 bge-m3？

Embedding 模型的选择：

| 模型 | 维度 | 优点 | 缺点 |
|------|------|------|------|
| OpenAI text-embedding-3 | 1536 | 效果好 | 💰 收费 + 需要联网 |
| bge-m3 | 1024 | ✅ 本地 + 免费 + 中文友好 | 需要 Ollama |
| nomic-embed-text | 768 | 轻量 | 中文效果一般 |

我选择 **bge-m3**：
- ✅ 完全本地运行（隐私）
- ✅ 中文效果优秀（北京智源出品）
- ✅ Ollama 一键安装

---

### 为什么用 Claude 做 summarization？

```python
summaries = summarize_with_claude(entries)
```

为什么不用 GPT 或开源模型？

**Claude 的优势：**
1. **理解上下文能力强**：能判断"这条笔记值得长期保存吗？"
2. **输出结构化好**：直接返回 JSON，方便解析
3. **我在用 Claude Code**：集成方便

当然，你也可以换成 GPT-4 或 Qwen：

```python
# 替换为 GPT-4
summaries = summarize_with_gpt(entries)

# 替换为本地 Ollama
summaries = summarize_with_ollama(entries, model="qwen2.5")
```

---

## 设计哲学：渐进式复杂度

很多人问："为什么不做一个 All-in-One 的 Web App？"

**我的设计理念是：渐进式复杂度**

### Level 1: 纯 Markdown（适合小白）

```bash
# 只写 markdown，不用数据库
vim ~/.my-memory/2026-02/2026-02-05.md

# 用 grep 搜索
grep -r "sqlite" ~/.my-memory/
```

**优点：** 零门槛，人类可读，Git 友好
**缺点：** 没有语义搜索

---

### Level 2: 数据库 + 向量搜索（适合 Geek）

```bash
# 安装 Ollama + bge-m3
./install.sh

# 提取长期记忆
python3 scripts/summarize_day.py --date 2026-02-05

# 语义搜索
python3 scripts/retrieve_memory.py --query "数据库问题"
```

**优点：** 语义搜索，效果更好
**缺点：** 需要安装 Ollama、配置数据库

---

### Level 3: Agent API（适合开发者）

```python
# 集成到你的 Agent 系统
memories = retrieve_memories(user_input, limit=5)
context = build_context(memories)
response = your_agent_call(context)
```

**优点：** AI Agent 有了长期记忆
**缺点：** 需要写代码集成

---

**每个人可以选择适合自己的复杂度**：
- 只想做笔记？→ Level 1
- 想要语义搜索？→ Level 2
- 想做 AI Agent？→ Level 3

---

## 实现细节：踩过的坑

### 坑 1: macOS 的 sqlite3 不支持扩展

**问题：**
```python
import sqlite3
conn.enable_load_extension(True)  # ❌ 报错
```

macOS 系统自带的 Python 的 sqlite3 模块，**不允许加载扩展**（安全限制）。

**解决方案：**
```python
try:
    from pysqlite3 import dbapi2 as sqlite3  # ✅ 用 pysqlite3
except ImportError:
    import sqlite3
```

安装：
```bash
pip3 install pysqlite3-binary
```

---

### 坑 2: sqlite-vec 的 rowid 和 UUID 的矛盾

**问题：**

sqlite-vec 的虚拟表必须用 **integer rowid**：
```sql
CREATE VIRTUAL TABLE vec_memories USING vec0(
    embedding float[1024]
);
-- rowid 必须是自增整数
```

但我想用 **UUID** 做主键（支持多设备合并）：
```sql
CREATE TABLE memories (
    uuid TEXT PRIMARY KEY  -- UUID 是字符串
);
```

**怎么办？**

**解决方案：加一个映射表**

```sql
-- 向量表（用 integer rowid）
CREATE VIRTUAL TABLE vec_memories USING vec0(...);

-- 记忆表（用 UUID）
CREATE TABLE memories (uuid TEXT PRIMARY KEY, ...);

-- 映射表
CREATE TABLE vec_memory_mapping (
    vec_rowid INTEGER,      -- 指向 vec_memories.rowid
    memory_uuid TEXT        -- 指向 memories.uuid
);
```

检索时通过映射表关联：
```sql
SELECT m.*
FROM vec_memories v
JOIN vec_memory_mapping map ON v.rowid = map.vec_rowid
JOIN memories m ON map.memory_uuid = m.uuid
WHERE vec_distance_cosine(v.embedding, ?) < 0.5
```

---

### 坑 3: Claude 的 JSON 输出不稳定

**问题：**

我让 Claude 输出 JSON 格式的摘要：

```
Prompt: "Return a JSON array: [{"type": "...", "summary": "..."}]"
```

但 Claude 有时会输出：
```
好的，我来提取记忆：

```json
[{"type": "knowledge", "summary": "..."}]
```

这样就破坏了 JSON 格式。
```

**解决方案：正则提取**

```python
# 提取 JSON（处理 markdown 代码块）
json_start = output.find("[")
json_end = output.rfind("]") + 1
json_str = output[json_start:json_end]
return json.loads(json_str)
```

---

## 开源了！

GitHub: https://github.com/yinwm/cortex-memory

**一键安装：**
```bash
git clone https://github.com/yinwm/cortex-memory.git
cd cortex-memory
./install.sh
```

**5 分钟搞定所有依赖**：
- ✅ Python 包（pysqlite3, sqlite-vec, numpy）
- ✅ Ollama + bge-m3 模型
- ✅ 数据库初始化

---

## 未来计划

### 短期（1-2 周）
- [ ] 完善文档（ARCHITECTURE.md, API.md）
- [ ] 添加单元测试
- [ ] 支持更多 embedding 模型（OpenAI, Cohere）
- [ ] Web UI（Gradio）用于调试

### 中期（1-2 月）
- [ ] 自动化 summarization（定时任务 / Git hook）
- [ ] 多设备同步方案（Git + conflict resolution）
- [ ] 记忆可视化（timeline, 关系图谱）
- [ ] 导出到 Obsidian / Notion

### 长期（想象空间）
- [ ] 多模态记忆（图片、音频、视频）
- [ ] 群体记忆（团队共享知识库）
- [ ] 记忆推荐（"你可能想回忆..."）
- [ ] 记忆遗忘机制（模拟人类的遗忘曲线）

---

## 写在最后

**这个项目的初衷很简单：**

我希望 AI 能像人一样，**记住重要的事情**。

不是记住所有细节（那是数据库），而是记住**值得记住的东西** —— 重要的决策、有价值的知识、踩过的坑。

**这也是我对 AI Agent 的一个设想：**

未来的 AI Agent 不应该是"对话完就忘"的工具，而应该是**能不断学习、积累经验的智能体**。

Cortex Memory 是我在这个方向上的一次尝试。

---

**如果你对这个项目感兴趣：**

- ⭐ Star 一下：https://github.com/yinwm/cortex-memory
- 🐛 提 Issue / PR
- 💬 告诉我你的使用场景和建议

**Let's build AI with long-term memory together!** 🧠

---

*本文作者：[@yinwm](https://github.com/yinwm)*
*项目地址：https://github.com/yinwm/cortex-memory*
*技术栈：Python 3.8+, SQLite, sqlite-vec, Ollama, Claude*
