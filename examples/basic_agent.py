#!/usr/bin/env python3
"""
Example: Basic AI agent with Cortex Memory integration

This demonstrates how to use Cortex Memory in your AI agent:
1. Retrieve relevant memories before processing input
2. Use memories as context for better responses
3. Extract and save new memories automatically
"""
import subprocess
import json
import re
from typing import List, Dict

def retrieve_memories(query: str, limit: int = 5) -> List[Dict]:
    """
    Retrieve relevant memories from Cortex.

    Args:
        query: Search query (can be natural language)
        limit: Number of results to return

    Returns:
        List of memory dictionaries with 'date', 'summary', 'score', etc.
    """
    try:
        result = subprocess.run(
            ["python3", "scripts/retrieve_memory.py",
             "--query", query,
             "--limit", str(limit)],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Parse output
        # Format: "1. [semantic] TYPE - Score: 0.863\n   📅 2026-02-05\n   📝 summary..."
        memories = []
        lines = result.stdout.split('\n')

        current_memory = {}
        for line in lines:
            if re.match(r'^\d+\. \[', line):
                # New result
                if current_memory:
                    memories.append(current_memory)

                # Parse score
                score_match = re.search(r'Score: ([\d.]+)', line)
                current_memory = {
                    'score': float(score_match.group(1)) if score_match else 0.0
                }
            elif line.strip().startswith('📅'):
                current_memory['date'] = line.split('📅')[1].strip()
            elif line.strip().startswith('📝'):
                current_memory['summary'] = line.split('📝')[1].strip()

        if current_memory:
            memories.append(current_memory)

        return memories

    except Exception as e:
        print(f"⚠️  Failed to retrieve memories: {e}")
        return []


def extract_memory(content: str, memory_type: str = "note") -> bool:
    """
    Extract and save important information to Cortex.

    Args:
        content: Content to save
        memory_type: Type of memory (task, knowledge, note)

    Returns:
        True if successful
    """
    try:
        # Call Claude CLI with extract-memory skill
        # (Assumes you have the skill installed)
        subprocess.run(
            ["claude",
             "-p", f"Extract and save this to memory:\n{content}\n\nType: {memory_type}",
             "--dangerously-skip-permissions"],
            timeout=60
        )
        return True
    except Exception as e:
        print(f"⚠️  Failed to extract memory: {e}")
        return False


def agent_think(user_input: str) -> str:
    """
    Main agent thinking loop with memory integration.

    Args:
        user_input: User's question or command

    Returns:
        Agent's response
    """
    print(f"🤔 Agent thinking about: {user_input}")

    # 1. Retrieve relevant memories
    print("🧠 Retrieving relevant memories...")
    memories = retrieve_memories(user_input, limit=3)

    # 2. Build context from memories
    context = ""
    if memories:
        context = "## Relevant past knowledge:\n"
        for i, mem in enumerate(memories, 1):
            context += f"{i}. [{mem.get('date', 'unknown')}] {mem.get('summary', '')[:100]}\n"
        print(f"✅ Found {len(memories)} relevant memories")
    else:
        print("ℹ️  No relevant memories found")

    # 3. Generate response (simplified - replace with your LLM call)
    response = generate_response(user_input, context)

    # 4. Extract new memories if response contains valuable info
    if should_save_to_memory(response):
        print("💾 Saving new insights to memory...")
        extract_memory(f"User asked: {user_input}\nAgent learned: {response}")

    return response


def generate_response(user_input: str, context: str) -> str:
    """
    Generate response using context from memories.

    Replace this with your actual LLM call (Claude, GPT, etc.)
    """
    # Simplified example - replace with real LLM call
    if context:
        prompt = f"{context}\n\nUser question: {user_input}\n\nResponse:"
    else:
        prompt = f"User question: {user_input}\n\nResponse:"

    # TODO: Call your LLM here
    # For demo purposes, just echo
    return f"Based on past knowledge, here's what I know: {context[:200]}..."


def should_save_to_memory(response: str) -> bool:
    """
    Decide if response contains valuable info worth saving.

    This is a simple heuristic - you can make it smarter with LLM.
    """
    # Simple heuristic: save if response is substantial
    return len(response) > 100


# Example usage
if __name__ == "__main__":
    # Example 1: Simple query
    print("=" * 60)
    print("Example 1: Query about sqlite-vec")
    print("=" * 60)
    response = agent_think("Tell me about sqlite-vec compatibility issues")
    print(f"\n🤖 Agent response:\n{response}\n")

    # Example 2: Save new knowledge
    print("=" * 60)
    print("Example 2: Learn and save new knowledge")
    print("=" * 60)
    extract_memory(
        "Cortex Memory uses bge-m3 for embeddings, which provides 1024-dim vectors",
        memory_type="knowledge"
    )
    print("✅ Knowledge saved\n")

    # Example 3: Retrieve and verify
    print("=" * 60)
    print("Example 3: Verify saved knowledge")
    print("=" * 60)
    memories = retrieve_memories("embedding model", limit=2)
    for mem in memories:
        print(f"  - {mem.get('summary', '')[:80]}...")
