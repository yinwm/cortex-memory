#!/bin/bash
set -e

echo "🧠 Installing Cortex Memory System..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check Python version
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# 2. Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 not found${NC}"
    echo "Please install pip3"
    exit 1
fi
echo -e "${GREEN}✅ pip3${NC}"

# 3. Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install pysqlite3-binary sqlite-vec numpy

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# 4. Check/Install Ollama
echo ""
echo "🦙 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama not found${NC}"
    echo "Installing Ollama..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
        echo "Please install Ollama manually: https://ollama.com"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Ollama installed${NC}"
fi

# 5. Start Ollama (if not running)
echo ""
echo "🚀 Starting Ollama service..."
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &> /dev/null &
    sleep 3
fi
echo -e "${GREEN}✅ Ollama running${NC}"

# 6. Pull bge-m3 model
echo ""
echo "🧠 Pulling bge-m3 embedding model..."
echo -e "${YELLOW}⏳ This may take a while (model size: ~567MB)${NC}"
ollama pull bge-m3
echo -e "${GREEN}✅ Model downloaded${NC}"

# 7. Check Claude CLI
echo ""
echo "🤖 Checking Claude Code CLI..."
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}⚠️  Claude CLI not found${NC}"
    echo "Please install Claude Code: https://github.com/anthropics/claude-code"
    echo ""
    echo -e "${YELLOW}Note: Claude CLI is required for summarization${NC}"
else
    echo -e "${GREEN}✅ Claude CLI installed${NC}"
fi

# 8. Initialize memory directory
echo ""
echo "📁 Initializing memory directory..."
MEMORY_DIR="$HOME/.my-memory"
mkdir -p "$MEMORY_DIR"
echo -e "${GREEN}✅ Created $MEMORY_DIR${NC}"

# 9. Initialize database
echo ""
echo "💾 Initializing database..."
python3 scripts/init_db.py
echo -e "${GREEN}✅ Database initialized${NC}"

# 10. Test installation
echo ""
echo "🧪 Testing installation..."
if python3 -c "import pysqlite3, sqlite_vec, numpy" 2>/dev/null; then
    echo -e "${GREEN}✅ All Python modules working${NC}"
else
    echo -e "${RED}❌ Module import failed${NC}"
    exit 1
fi

# 11. Done!
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📚 Quick Start:"
echo ""
echo "1. Create a daily note:"
echo "   vim ~/.my-memory/2026-02/2026-02-05.md"
echo ""
echo "2. Summarize to long-term memory:"
echo "   python3 scripts/summarize_day.py --date 2026-02-05"
echo ""
echo "3. Search your memories:"
echo "   python3 scripts/retrieve_memory.py --query \"your search\""
echo ""
echo "📖 Documentation: docs/INSTALL.md"
echo "🤖 Agent examples: examples/"
echo ""
