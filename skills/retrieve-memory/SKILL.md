---
name: retrieve-memory
description: Search long-term memory database using semantic + keyword hybrid search. Use when user asks to search memory, retrieve memories, find past information, recall knowledge, or query the memory system. Supports searching for tasks, knowledge, decisions, and insights stored in the memory database.
---

# Retrieve Memory

从长期记忆数据库中检索相关信息，使用语义搜索 + 关键词搜索的混合算法。

## 使用方法

### 基本搜索

```bash
python3 ~/.claude/skills/retrieve-memory/scripts/retrieve_memory.py --query "搜索内容"
```

### 自定义返回数量

```bash
# 返回 5 条结果（默认 10 条）
python3 ~/.claude/skills/retrieve-memory/scripts/retrieve_memory.py --query "搜索内容" --limit 5

# 返回 20 条结果
python3 ~/.claude/skills/retrieve-memory/scripts/retrieve_memory.py --query "搜索内容" --limit 20
```

### 调整搜索权重

```bash
# 50% 语义 + 50% 关键词（默认 70% 语义 + 30% 关键词）
python3 ~/.claude/skills/retrieve-memory/scripts/retrieve_memory.py --query "搜索内容" --semantic-weight 0.5

# 90% 语义 + 10% 关键词（更侧重语义）
python3 ~/.claude/skills/retrieve-memory/scripts/retrieve_memory.py --query "搜索内容" --semantic-weight 0.9
```

## 工作原理

检索算法使用混合策略：

1. **语义搜索（70%）**：使用 bge-m3 embeddings + sqlite-vec 进行向量相似度搜索
2. **关键词搜索（30%）**：在最近 3 天的记忆文件中进行关键词匹配
3. **结果合并**：按加权分数排序，返回最相关的结果

## 输出格式

```
✨ Top 3 results:

1. [semantic] KNOWLEDGE - Score: 0.922
   📅 2026-02-05
   📝 Memory 系统采用三阶段架构：Phase 1 使用 daily files...

2. [keyword] TASK - Score: 0.650
   📅 2026-02-04
   📝 完成 extract-memory skill 开发...
```

- **[semantic]** 或 **[keyword]**：结果来源
- **类型**：KNOWLEDGE、TASK、NOISE、NOTE
- **Score**：相关性分数（0-1，越高越相关）
- **日期**：记忆创建日期
- **内容**：记忆摘要

## 数据位置

- **数据库**：`~/.my-memory/my-memories.db`
- **每日文件**：`~/.my-memory/YYYY-MM/YYYY-MM-DD.md`
- **检索脚本**：`~/.claude/skills/retrieve-memory/scripts/retrieve_memory.py`

## 前置要求

1. **Ollama bge-m3 模型运行**：
   ```bash
   ollama run bge-m3
   ```

2. **数据库已初始化**：
   运行过 `summarize_day.py` 将每日记忆提取到数据库

## 使用场景示例

- "查找我们之前讨论的 Memory 系统设计"
- "搜索关于 sqlite-vec 的所有记忆"
- "我有哪些未完成的任务？"
- "回忆一下昨天讨论的内容"
