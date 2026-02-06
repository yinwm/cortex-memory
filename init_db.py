#!/usr/bin/env python3
"""
Initialize Cortex Memory database.
Creates tables and sets up sqlite-vec extension.
"""
try:
    from pysqlite3 import dbapi2 as sqlite3
except ImportError:
    import sqlite3
import sqlite_vec
from pathlib import Path

# Configuration
MEMORY_DIR = Path.home() / ".my-memory"
DB_PATH = MEMORY_DIR / "my-memories.db"

def init_db():
    """Initialize SQLite database with sqlite-vec"""
    print(f"📊 Initializing database at {DB_PATH}")

    # Ensure directory exists
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    cursor = conn.cursor()

    # Create personal_info table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            user_name TEXT NOT NULL DEFAULT '用户',
            device TEXT NOT NULL DEFAULT 'default-device',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert default personal info if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO personal_info (id, user_name, device)
        VALUES (1, '用户', 'default-device')
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

    # Create index on date for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_date ON memories(date)
    """)

    # Create virtual table for vector search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories
        USING vec0(
            embedding float[1024]
        )
    """)

    # Create mapping table: vec_rowid (INTEGER) <-> memory_uuid (TEXT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vec_memory_mapping (
            vec_rowid INTEGER PRIMARY KEY,
            memory_uuid TEXT NOT NULL UNIQUE,
            FOREIGN KEY (memory_uuid) REFERENCES memories(uuid)
        )
    """)

    conn.commit()

    # Print stats
    cursor.execute("SELECT COUNT(*) FROM memories")
    count = cursor.fetchone()[0]

    conn.close()

    print(f"✅ Database initialized successfully")
    print(f"   Tables: personal_info, memories, vec_memories, vec_memory_mapping")
    print(f"   Current memories: {count}")

    return DB_PATH

if __name__ == "__main__":
    init_db()
