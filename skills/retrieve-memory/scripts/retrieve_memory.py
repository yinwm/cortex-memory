#!/usr/bin/env python3
"""
Retrieve memories from database using semantic search + keyword search.
Usage: python3 retrieve_memory.py --query "your search query"
"""
import sys
import argparse
try:
    from pysqlite3 import dbapi2 as sqlite3
except ImportError:
    import sqlite3
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np
import sqlite_vec

# Configuration
MEMORY_DIR = Path.home() / ".my-memory"
DB_PATH = MEMORY_DIR / "my-memories.db"
OLLAMA_MODEL = "bge-m3"
EMBEDDING_DIM = 1024

def get_embedding(text):
    """Get embedding from Ollama (using HTTP API)"""
    try:
        import urllib.request
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

def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors"""
    try:
        a_np = np.array(a)
        b_np = np.array(b)
        return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
    except:
        return 0.0

def semantic_search(query_embedding, limit=10):
    """Search memories by semantic similarity using sqlite-vec"""
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    cursor = conn.cursor()

    # Convert query embedding to numpy array with float32
    query_array = np.array(query_embedding, dtype=np.float32)

    # Use sqlite-vec to perform vector search with cosine distance
    # Join through vec_memory_mapping to link vec_rowid <-> memory_uuid
    cursor.execute("""
        SELECT
            m.uuid,
            m.date,
            m.type,
            m.summary,
            m.importance,
            m.metadata,
            vec_distance_cosine(v.embedding, ?) as distance
        FROM vec_memories v
        JOIN vec_memory_mapping map ON v.rowid = map.vec_rowid
        JOIN memories m ON map.memory_uuid = m.uuid
        WHERE v.embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT ?
    """, (query_array, limit))

    results = []
    for row in cursor.fetchall():
        memory_uuid, date, mem_type, summary, importance, metadata_json, distance = row

        # Convert cosine distance to similarity: similarity = 1 - distance
        similarity = 1.0 - distance

        # Parse metadata to get tags
        try:
            metadata = json.loads(metadata_json) if metadata_json else {}
            tags = metadata.get("tags", [])
        except:
            tags = []

        results.append({
            "id": memory_uuid,
            "date": date,
            "type": mem_type,
            "summary": summary,
            "importance": importance,
            "tags": tags,
            "score": similarity,
            "source": "semantic"
        })

    conn.close()
    return results

def keyword_search(query: str, days=3):
    """Search recent memory files for keywords"""
    results = []
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        year_month = date.strftime("%Y-%m")

        memory_file = MEMORY_DIR / year_month / f"{date_str}.md"

        if not memory_file.exists():
            continue

        # Read file and search for keywords
        content = memory_file.read_text(encoding='utf-8')

        # Simple keyword matching (split query into terms)
        query_terms = query.lower().split()
        entry_matches = []

        current_entry = []
        current_header = None

        for line in content.splitlines():
            if line.startswith("## ") and " - " in line:
                # Save previous entry
                if current_entry and current_header:
                    entry_text = "\n".join(current_entry).lower()
                    # Count matching keywords
                    match_count = sum(1 for term in query_terms if term in entry_text)
                    if match_count > 0:
                        entry_matches.append({
                            "header": current_header,
                            "content": "\n".join(current_entry),
                            "match_count": match_count
                        })

                current_header = line
                current_entry = []
            else:
                current_entry.append(line)

        # Save last entry
        if current_entry and current_header:
            entry_text = "\n".join(current_entry).lower()
            match_count = sum(1 for term in query_terms if term in entry_text)
            if match_count > 0:
                entry_matches.append({
                    "header": current_header,
                    "content": "\n".join(current_entry),
                    "match_count": match_count
                })

        # Add to results
        for match in entry_matches:
            results.append({
                "date": date_str,
                "header": match["header"],
                "summary": match["content"][:200] + "..." if len(match["content"]) > 200 else match["content"],
                "score": match["match_count"] / len(query_terms),  # Normalized score
                "source": "keyword"
            })

    # Sort by match count
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]

def merge_results(semantic_results, keyword_results, semantic_weight=0.7):
    """Merge semantic and keyword results with weighted scoring"""
    # Use a dictionary to avoid duplicates
    merged = {}

    # Add semantic results
    for result in semantic_results:
        memory_id = result["id"]
        merged[memory_id] = {
            **result,
            "final_score": result["score"] * semantic_weight
        }

    # Add keyword results and update scores
    for result in keyword_results:
        # Try to find matching semantic result by summary similarity
        found = False
        for memory_id, merged_result in merged.items():
            if result["date"] == merged_result["date"]:
                # Same date, assume it's the same memory
                merged[memory_id]["final_score"] += result["score"] * (1 - semantic_weight)
                merged[memory_id]["keyword_boost"] = True
                found = True
                break

        if not found:
            # New result from keyword search only
            new_id = f"kw-{result['date']}"
            merged[new_id] = {
                **result,
                "final_score": result["score"] * (1 - semantic_weight),
                "keyword_boost": False
            }

    # Convert back to list and sort
    results = list(merged.values())
    results.sort(key=lambda x: x["final_score"], reverse=True)

    return results[:10]

def main():
    parser = argparse.ArgumentParser(description="Retrieve memories from database")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Number of results to return (default: 10)")
    parser.add_argument("--semantic-weight", type=float, default=0.7, help="Weight for semantic search (0-1)")
    args = parser.parse_args()

    print(f"🔍 Searching for: {args.query}\n")

    # Get query embedding
    print("🧠 Computing query embedding...")
    query_embedding = get_embedding(args.query)

    if not query_embedding:
        print("❌ Failed to get query embedding")
        sys.exit(1)

    # Semantic search
    print("🔎 Semantic search (SQLite)...")
    semantic_results = semantic_search(query_embedding, limit=args.limit)
    print(f"   Found {len(semantic_results)} results\n")

    # Keyword search
    print("🔑 Keyword search (recent 3 days)...")
    keyword_results = keyword_search(args.query)
    print(f"   Found {len(keyword_results)} results\n")

    # Merge results
    print("🔀 Merging results...")
    final_results = merge_results(semantic_results, keyword_results, args.semantic_weight)
    final_results = final_results[:args.limit]  # Apply limit after merging

    # Display results
    print(f"\n✨ Top {len(final_results)} results:\n")

    for i, result in enumerate(final_results, 1):
        tags_str = " ".join(result.get('tags', []))
        print(f"{i}. [{result['source']}] {result.get('type', 'note')} - Score: {result['final_score']:.3f}")
        print(f"   📅 {result['date']}")
        if tags_str:
            print(f"   🏷️  {tags_str}")
        print(f"   📝 {result['summary'][:100]}...")
        print()

if __name__ == "__main__":
    main()
