---
name: extract-memory
description: Extract valuable information from conversation context and save to daily memory files. Use when user explicitly asks to save/remember something, conversation contains important decisions/insights/action items, end of meaningful conversation, or user says "save to memory"/"remember this".
---

# Extract Memory

智能提取对话中的有价值信息并保存到每日记忆文件。

## 工作原理

**重要**：本 skill **不使用 Python 脚本**，而是**直接使用 Write 工具**写入记忆文件。

- ✅ **正确方式**：使用 `Write` 工具直接追加内容到今天的记忆文件
- ❌ **错误方式**：不要调用 `python3 extract_memory.py` 或类似脚本（此脚本不存在）

与 `retrieve-memory` 的区别：
- **extract-memory**（本 skill）：使用 `Write` 工具写入文件
- **retrieve-memory**：调用 Python 脚本进行向量搜索

## 触发条件

- 用户明确要求保存记忆（"记住这个"、"存到 memory"等）
- 对话包含重要决策、洞察或行动项
- 对话结束时发现有价值的内容
- 用户说类似 "extract memory" 的指令

## 判断标准

**值得保存的内容：**
- ✅ **任务和行动项**：具体要做什么、如何做
- ✅ **重要洞察和决策**：为什么这么做、学到了什么
- ✅ **有价值的想法和思路**：未来的方向、改进点
- ✅ **关键上下文信息**：项目背景、架构决策、依赖关系

**不值得保存的内容（DO NOT SAVE）：**
- ❌ **操作记录**："已加入队列"、"已创建任务"、"处理中"、"等待执行"
- ❌ **系统通知**："任务完成"、"文件已保存"、"同步成功"
- ❌ **中间状态**：临时的调试过程、尝试性命令
- ❌ **简单确认**："好的"、"明白了"、"收到"
- ❌ **闲聊**："哈哈"、"测试"、"hello"
- ❌ **URL 本身**：如果已经在队列系统或任务卡片中追踪
- ❌ **重复信息**：今天文件中已存在类似内容
- ❌ **元操作**："正在调用 skill"、"执行脚本中"等系统内部流程

**关键判断问题**：
> "3 个月后我还需要这个信息吗？"
> - 如果 YES → 保存
> - 如果 NO → 跳过

## 保存格式

保存到 `~/.my-memory/YYYY-MM/YYYY-MM-DD.md`（按年月分组），格式：

```markdown
## HH:MM - {简洁标题}
{summary}

**Tags**: #tag1 #tag2 #tag3
**Importance**: 0.1-1.0
```

- **标题**：简洁概括内容（1-10 个词）
- **Summary**：1-2 句话详细描述
- **Tags**：自由打标签，用于分类和检索
- **Importance**：重要性评分 0.1-1.0（可选）

## 执行流程

1. **分析对话**：回顾对话历史，识别有价值的信息
2. **分类判断**：判断每个信息点的类型和重要性
3. **写入文件**（关键步骤）：
   - 使用 `Write` 工具（**不要用 Bash 调用脚本**）
   - 目标路径：`~/.my-memory/YYYY-MM/YYYY-MM-DD.md`（今天的日期）
   - 操作模式：**追加**（如果文件存在，在末尾追加；如果不存在，创建新文件）
   - 格式：按照下面的模板格式写入
4. **反馈用户**：告诉用户保存了什么内容

## 示例

### ✅ 正例：应该保存

**用户说**："记住 sqlite-vec 的安装问题"

你分析对话，提取关键点并写入：
```markdown
## 13:40 - sqlite-vec macOS 兼容性问题
macOS 系统自带 Python 不支持 SQLite 扩展加载，需要用 pysqlite3 替代系统 sqlite3 模块

**Tags**: #sqlite #database #macos #python #troubleshooting
**Importance**: 0.8
```

### ❌ 反例：不应该保存

**场景 1**："URL 已加入队列"
```
❌ DON'T SAVE: "微信文章已加入异步处理队列"
原因：这是操作记录，队列系统自己会追踪
```

**场景 2**："任务已创建"
```
❌ DON'T SAVE: "功迪视频任务已创建，包含 7 个子任务"
原因：任务卡片本身已经存在，不需要重复记录
```

**场景 3**："正在处理"
```
❌ DON'T SAVE: "正在调用 /task skill 处理任务"
原因：这是系统内部流程，不是知识
```

**场景 4**："简单通知"
```
❌ DON'T SAVE: "任务完成"、"文件已保存"
原因：3 个月后你不需要知道"某天某任务完成了"
```

## 注意事项

### 关键约束
- **⚠️ 不要调用脚本**：本 skill 不使用 `extract_memory.py`，直接用 `Write` 工具写入文件
- **使用 Write 工具**：必须使用 `Write` 工具，不能用 `Bash` + `echo` 或其他方式

### 内容质量
- **不要过度保存**：只保存真正有价值的内容
- **简洁明了**：标题控制在 1-10 个词，summary 1-2 句话
- **标签灵活**：根据内容自由打标签，常用标签：#tech #design #decision #bugfix #idea
- **保持上下文**：保存时保留必要的背景信息
- **避免重复**：检查今天文件是否已有类似内容
