# Installation Guide

Complete installation guide for Cortex Memory on different platforms.

## Table of Contents

- [Quick Install (Recommended)](#quick-install-recommended)
- [Manual Installation](#manual-installation)
- [Docker Installation](#docker-installation)
- [Troubleshooting](#troubleshooting)

---

## Quick Install (Recommended)

### macOS / Linux

```bash
git clone https://github.com/YOUR_USERNAME/cortex-memory.git
cd cortex-memory
chmod +x install.sh
./install.sh
```

The script will:
1. ✅ Check Python 3.8+
2. ✅ Install Python dependencies (pysqlite3, sqlite-vec, numpy)
3. ✅ Install Ollama (if not present)
4. ✅ Download bge-m3 model (~567MB)
5. ✅ Install Claude Code CLI (reminder if missing)
6. ✅ Initialize database

**Total time: ~5-10 minutes** (depending on download speed)

---

## Manual Installation

### Step 1: Prerequisites

**Required:**
- Python 3.8 or higher
- pip3

**Check your version:**
```bash
python3 --version
pip3 --version
```

### Step 2: Install Python Dependencies

```bash
pip3 install pysqlite3-binary sqlite-vec numpy
```

**Note for macOS users:**
- Use `pysqlite3-binary` instead of `pysqlite3`
- System Python's sqlite3 doesn't support extensions

### Step 3: Install Ollama

**macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Verify installation:**
```bash
ollama --version
```

### Step 4: Download bge-m3 Model

```bash
# Start Ollama service (if not running)
ollama serve &

# Pull model
ollama pull bge-m3
```

**Model size:** ~567MB

### Step 5: Install Claude Code CLI

Follow instructions at: https://github.com/anthropics/claude-code

**Verify installation:**
```bash
claude --version
```

### Step 6: Initialize Database

```bash
cd cortex-memory
python3 init_db.py
```

This creates `~/.my-memory/my-memories.db` with required tables.

### Step 7: Verify Installation

```bash
# Test retrieval (should return empty results if no data)
python3 skills/retrieve-memory/scripts/retrieve_memory.py --query "test"
```

---

## Docker Installation

Coming soon.

---

## Platform-Specific Notes

### macOS

**Issue: sqlite3 module doesn't support extensions**

**Solution:**
```bash
pip3 install pysqlite3-binary
```

Code will automatically use `pysqlite3` if available:
```python
try:
    from pysqlite3 import dbapi2 as sqlite3
except ImportError:
    import sqlite3
```

**Issue: Ollama not starting**

**Solution:**
```bash
# Check if already running
pgrep -x ollama

# Kill existing process
pkill ollama

# Start fresh
ollama serve
```

### Linux

**Issue: Permission denied for Ollama install**

**Solution:**
```bash
# Run install with sudo
curl -fsSL https://ollama.com/install.sh | sudo sh
```

**Issue: Ollama service not starting**

**Solution:**
```bash
# Enable and start systemd service
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Windows (WSL)

Cortex Memory works on Windows via WSL2.

1. Install WSL2: https://docs.microsoft.com/en-us/windows/wsl/install
2. Follow Linux installation steps inside WSL2

---

## Troubleshooting

### Python Dependencies

**Error: `No module named 'pysqlite3'`**

```bash
pip3 install pysqlite3-binary
```

**Error: `No module named 'sqlite_vec'`**

```bash
pip3 install sqlite-vec
```

**Error: `No module named 'numpy'`**

```bash
pip3 install numpy
```

### Ollama Issues

**Error: `connection refused localhost:11434`**

Ollama service not running:
```bash
ollama serve &
```

**Error: `model bge-m3 not found`**

Model not downloaded:
```bash
ollama pull bge-m3
```

**Error: `timeout waiting for ollama`**

Increase timeout or check Ollama logs:
```bash
# Check logs
ollama list
ollama ps
```

### Database Issues

**Error: `no such table: memories`**

Database not initialized:
```bash
python3 init_db.py
```

**Error: `database is locked`**

Another process using database:
```bash
# Find process
lsof ~/.my-memory/my-memories.db

# Kill if necessary
kill -9 <PID>
```

### Claude CLI Issues

**Error: `claude: command not found`**

Claude CLI not installed. Install from:
https://github.com/anthropics/claude-code

**Error: `API key not configured`**

Set up Claude API key:
```bash
claude configure
```

---

## Post-Installation

### 1. Create Your First Memory

```bash
mkdir -p ~/.my-memory/$(date +%Y-%m)
cat > ~/.my-memory/$(date +%Y-%m)/$(date +%Y-%m-%d).md << 'EOF'
## 14:30 - knowledge
Cortex Memory installed successfully! Ready to build long-term AI memory.

**Tags**: #cortex #setup #milestone
**Importance**: 0.9
EOF
```

### 2. Summarize to Database

```bash
python3 skills/extract-memory/scripts/summarize_day.py --date $(date +%Y-%m-%d)
```

### 3. Search

```bash
python3 skills/retrieve-memory/scripts/retrieve_memory.py --query "cortex setup"
```

---

## Updating

```bash
cd cortex-memory
git pull
pip3 install --upgrade -r requirements.txt
```

---

## Uninstallation

```bash
# Remove Python packages
pip3 uninstall pysqlite3-binary sqlite-vec numpy

# Remove Ollama (macOS)
brew uninstall ollama

# Remove memory data (⚠️ this deletes all your memories)
rm -rf ~/.my-memory

# Remove cortex code
rm -rf cortex-memory/
```

---

## Next Steps

- [Architecture Overview](ARCHITECTURE.md)
- [API Reference](API.md)
- [Examples](../examples/)
