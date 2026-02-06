# Cortex Memory

A semantic long-term memory system for humans and AI agents.

> **Cortex** remembers what matters, so you (and your agents) don't have to.

## 🎯 What is Cortex?

Cortex is a **persistent memory layer** that:
- 📝 Automatically captures valuable information from your daily notes
- 🧠 Uses semantic search to find relevant memories (not just keywords)
- 🤖 Provides API for AI agents to access long-term knowledge
- 🔄 Designed for both **personal use** and **multi-agent systems**

### Use Cases

**For Individuals:**
- Daily journaling with intelligent retrieval
- Personal knowledge base that grows with you
- Never lose important insights again

**For AI Agents:**
- Persistent memory across conversation sessions
- Shared knowledge base for multi-agent systems
- Context-aware decision making

---

## 🏗️ Architecture

```
Daily Notes (Markdown)
    ↓ summarize_day.py
Long-term Memory (SQLite + Vectors)
    ↓ retrieve_memory.py
Semantic Search Results
```

### Tech Stack

- **Storage**: SQLite + [sqlite-vec](https://github.com/asg017/sqlite-vec)
- **Embeddings**: [bge-m3](https://huggingface.co/BAAI/bge-m3) via Ollama (1024-dim)
- **Summarization**: Claude API via [Claude Code CLI](https://github.com/anthropics/claude-code)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.com/) (for embeddings)
- [Claude Code CLI](https://github.com/anthropics/claude-code) (for summarization)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/cortex-memory.git
cd cortex-memory

# 2. Run install script
chmod +x install.sh
./install.sh

# 3. Verify installation
python3 init_db.py
```

### Basic Usage

#### 1. Write daily notes

Create a file at `~/.my-memory/2026-02/2026-02-05.md`:

```markdown
## 14:30 - knowledge
Discovered that sqlite-vec requires pysqlite3 on macOS because system Python doesn't support extension loading.

**Tags**: #sqlite #database #macos
**Importance**: 0.8

## 15:00 - task ✅
Completed Memory system architecture design with three-phase approach: daily files → summarization → vector database

**Tags**: #project #architecture
**Importance**: 0.9
```

#### 2. Summarize to long-term memory

```bash
python3 skills/extract-memory/scripts/summarize_day.py --date 2026-02-05
```

This will:
- Read your daily notes
- Use Claude to extract long-term valuable information
- Generate embeddings via Ollama
- Store in SQLite with vector index

#### 3. Search your memories

```bash
# Semantic search
python3 skills/retrieve-memory/scripts/retrieve_memory.py --query "sqlite 兼容性问题"

# Adjust search parameters
python3 skills/retrieve-memory/scripts/retrieve_memory.py --query "database" --limit 5 --semantic-weight 0.9
```

---

## 🤖 For Agent Developers

### Python API

```python
import subprocess
import json

def retrieve_memories(query: str, limit: int = 10):
    """Retrieve relevant memories for agent context"""
    result = subprocess.run(
        ["python3", "skills/retrieve-memory/scripts/retrieve_memory.py",
         "--query", query, "--limit", str(limit)],
        capture_output=True,
        text=True
    )
    return parse_output(result.stdout)

def agent_think(user_input):
    # Get relevant memories
    memories = retrieve_memories(user_input, limit=5)

    # Build context
    context = "\n".join([m["summary"] for m in memories])

    # Call your agent with context
    response = your_agent_call(f"Context: {context}\n\nUser: {user_input}")

    return response
```

### Claude Code Skill

Cortex includes two skills for Claude Code:

1. **extract-memory**: Automatically save valuable information
2. **retrieve-memory**: Search long-term memories

See [skills/](skills/) for installation.

---

## 📚 Documentation

- [Installation Guide](docs/INSTALL.md) - Detailed setup for macOS/Linux/Docker
- [Architecture](docs/ARCHITECTURE.md) - System design and rationale
- [API Reference](docs/API.md) - Python API and CLI usage
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

---

## 🛠️ Advanced Features

### Docker Deployment

```bash
docker-compose up -d
```

### Custom Embedding Models

```bash
# Use a different Ollama model
export OLLAMA_MODEL=mxbai-embed-large
python3 skills/extract-memory/scripts/summarize_day.py --date 2026-02-05
```

### Multi-Device Sync

```bash
cd ~/.my-memory
git init
git remote add origin YOUR_REPO
git push -u origin main
```

On another device:
```bash
git clone YOUR_REPO ~/.my-memory
```

SQLite with UUID-based merge handles conflicts gracefully.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

### Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black skills/ tests/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [sqlite-vec](https://github.com/asg017/sqlite-vec) by Alex Garcia
- [bge-m3](https://huggingface.co/BAAI/bge-m3) by Beijing Academy of AI
- [Claude Code](https://github.com/anthropics/claude-code) by Anthropic

---

## ⚡ Quick Links

- [Examples](examples/) - Integration examples
- [Skills](skills/) - Claude Code skills
- [FAQ](docs/FAQ.md) - Frequently asked questions

**Built with 🧠 by [@yinwm](https://github.com/yinwm)**
