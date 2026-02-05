#!/usr/bin/env python3
"""
Summarize daily memory and extract long-term memories to SQLite.
Usage: python3 summarize_day.py --date 2026-02-05
"""
import sys
import argparse
try:
    from pysqlite3 import dbapi2 as sqlite3
except ImportError:
    import sqlite3
import json
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
import sqlite_vec

# Configuration
MEMORY_DIR = Path.home() / ".my-memory"
DB_PATH = MEMORY_DIR / "my-memories.db"
OLLAMA_MODEL = "bge-m3"
EMBEDDING_DIM = 1024  # bge-m3 uses 1024 dimensions

def get_memory_file(date_str):
    """Get memory file path for given date (YYYY-MM-DD format)"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year_month = date_obj.strftime("%Y-%m")
        memory_file = MEMORY_DIR / year_month / f"{date_str}.md"

        if not memory_file.exists():
            print(f"❌ Memory file not found: {memory_file}")
            return None

        return memory_file
    except ValueError:
        print(f"❌ Invalid date format: {date_str}. Use YYYY-MM-DD")
        return None

def read_memory_entries(memory_file):
    """Read and parse memory entries from file"""
    content = memory_file.read_text(encoding='utf-8')
    entries = []

    current_entry = []
    current_time = None
    current_type = None

    for line in content.splitlines():
        if line.startswith("## ") and " - " in line:
            # Save previous entry
            if current_entry:
                entries.append({
                    "time": current_time,
                    "type": current_type,
                    "content": "\n".join(current_entry).strip()
                })

            # Parse new entry
            parts = line[3:].split(" - ")
            current_time = parts[0].strip()
            rest = parts[1] if len(parts) > 1 else ""

            # Extract type (task, knowledge, noise, note)
            for t in ["task", "knowledge", "noise", "note"]:
                if t in rest.lower():
                    current_type = t
                    break
            else:
                current_type = "note"

            current_entry = []
        else:
            current_entry.append(line)

    # Save last entry
    if current_entry:
        entries.append({
            "time": current_time,
            "type": current_type,
            "content": "\n".join(current_entry).strip()
        })

    return entries

def summarize_with_claude(entries):
    """Use Claude to summarize and extract long-term memories"""
    print("🤖 Calling Claude to summarize...")

    # Build prompt
    entries_text = "\n\n".join([
        f"[{e['type']}] {e['content']}"
        for e in entries
    ])

    prompt = f"""
You are a Memory Summarization Agent.
Your goal is to analyze the day's memory entries and extract what's worth storing in LONG-TERM memory.

# Today's Memory Entries:
{entries_text}

# Instructions:
1. **IDENTIFY** which entries contain long-term value:
   - ✅ Important decisions and insights
   - ✅ Knowledge worth retaining
   - ✅ Action items or tasks
   - ❌ Temporary noise or trivial thoughts

2. **For each valuable entry, provide**:
   - type: free-form label (e.g., "sqlite-vec安装", "系统架构", "Bug修复")
   - summary: concise 1-2 sentence summary
   - importance: score 0-1 (how important is this?)
   - tags: array of relevant tags (e.g., ["#tech", "#sqlite", "#database"])

3. **OUTPUT FORMAT**: Return a JSON array:
```json
[
  {{
    "type": "sqlite-vec 升级",
    "summary": "从 Python 余弦相似度升级到 sqlite-vec 高性能向量搜索",
    "importance": 0.9,
    "tags": ["#tech", "#sqlite", "#optimization"],
    "original_type": "knowledge",
    "original_time": "13:30"
  }}
]
```

Only include entries that have long-term value. Skip trivial content.
"""

    # Call Claude CLI
    cmd = [
        "claude",
        "-p", prompt,
        "--dangerously-skip-permissions"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        output = result.stdout

        # Extract JSON from output (handle markdown code blocks)
        # Try to find JSON array
        json_start = output.find("[")
        json_end = output.rfind("]") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = output[json_start:json_end]
            try:
                return json.loads(json_str)
            except:
                # Try removing markdown code blocks
                import re
                # Remove ```json and ``` markers
                json_clean = re.sub(r'```(?:json)?\n?', '', output)
                json_start = json_clean.find("[")
                json_end = json_clean.rfind("]") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = json_clean[json_start:json_end]
                    return json.loads(json_str)

        print("⚠️  No JSON found in Claude output")
        print("Raw output (first 500 chars):")
        print(output[:500])
        return []

    except subprocess.TimeoutExpired:
        print("❌ Claude timed out")
        return []
    except Exception as e:
        print(f"❌ Error calling Claude: {e}")
        return []

def get_embedding(text):
    """Get embedding from Ollama (using HTTP API)"""
    try:
        import urllib.request
        import json

        url = "http://localhost:11434/api/embeddings"
        data = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": text
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            embedding = result.get("embedding", [])

        return embedding

    except Exception as e:
        print(f"⚠️  Warning: Could not get embedding: {e}")
        return []

def init_db():
    """Initialize SQLite database with sqlite-vec"""
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    cursor = conn.cursor()

    # Create personal_info table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            user_name TEXT NOT NULL DEFAULT '大铭',
            device TEXT NOT NULL DEFAULT 'macbook-m3',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default personal info if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO personal_info (id, user_name, device)
        VALUES (1, '大铭', 'macbook-m3')
    """)

    # Create memories table with UUID as primary key (for multi-device merge)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            uuid TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            summary TEXT NOT NULL,
            importance REAL,
            embedding_json TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create virtual table for vector search with integer rowid + uuid reference
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories
        USING vec0(
            embedding float[1024]
        )
    """)

    # Create a mapping table: vec_rowid (INTEGER) <-> memory_uuid (TEXT)
    # This allows sqlite-vec to use integer rowids while we keep UUID for merges
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vec_memory_mapping (
            vec_rowid INTEGER PRIMARY KEY,
            memory_uuid TEXT NOT NULL UNIQUE,
            FOREIGN KEY (memory_uuid) REFERENCES memories(uuid)
        )
    """)

    conn.commit()
    return conn

def save_memories(conn, date_str, summaries):
    """Save summarized memories to database"""
    cursor = conn.cursor()

    for item in summaries:
        summary = item.get("summary", "")
        mem_type = item.get("type", "note")
        importance = item.get("importance", 0.5)
        tags = item.get("tags", [])

        # Generate UUID as primary key (for multi-device merge)
        memory_uuid = str(uuid.uuid4())

        # Get embedding
        embedding = get_embedding(summary)
        embedding_json = json.dumps(embedding) if embedding else None

        # Metadata (store tags here for future filtering)
        metadata = json.dumps({
            "original_time": item.get("original_time"),
            "original_type": item.get("original_type"),
            "tags": tags
        })

        # Insert into memories table (UUID is primary key)
        cursor.execute("""
            INSERT INTO memories (uuid, date, type, summary, importance, embedding_json, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (memory_uuid, date_str, mem_type, summary, importance, embedding_json, metadata))

        # Insert into vec_memories for efficient vector search
        if embedding:
            try:
                # Convert embedding list to float32 numpy array for sqlite-vec
                import numpy as np
                embedding_array = np.array(embedding, dtype=np.float32)

                # Insert into vec_memories (auto-increments rowid)
                cursor.execute("""
                    INSERT INTO vec_memories (embedding)
                    VALUES (?)
                """, (embedding_array,))

                # Get the auto-increment vec_rowid
                vec_rowid = cursor.lastrowid

                # Map vec_rowid to memory_uuid
                cursor.execute("""
                    INSERT INTO vec_memory_mapping (vec_rowid, memory_uuid)
                    VALUES (?, ?)
                """, (vec_rowid, memory_uuid))

            except Exception as e:
                print(f"⚠️  Warning: Could not insert into vec_memories: {e}")

    conn.commit()
    print(f"✅ Saved {len(summaries)} memories to database")

def main():
    parser = argparse.ArgumentParser(description="Summarize daily memory to long-term storage")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()

    print(f"📅 Processing date: {args.date}\n")

    # Step 1: Read memory file
    memory_file = get_memory_file(args.date)
    if not memory_file:
        sys.exit(1)

    print(f"📖 Reading: {memory_file}")
    entries = read_memory_entries(memory_file)
    print(f"   Found {len(entries)} entries\n")

    if not entries:
        print("❌ No entries found")
        sys.exit(1)

    # Step 2: Summarize with Claude
    summaries = summarize_with_claude(entries)

    if not summaries:
        print("❌ No long-term memories extracted")
        sys.exit(1)

    print(f"\n✨ Extracted {len(summaries)} long-term memories:")
    for s in summaries:
        print(f"   - [{s['type']}] {s['summary'][:60]}...")

    # Step 3: Save to database
    conn = init_db()
    save_memories(conn, args.date, summaries)
    conn.close()

    print(f"\n📊 Database: {DB_PATH}")
    print("✅ Done!")

if __name__ == "__main__":
    main()
