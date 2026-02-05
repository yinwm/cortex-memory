#!/usr/bin/env python3
"""
Example: Multi-agent system with shared Cortex Memory

This demonstrates:
1. Multiple agents sharing the same memory system
2. Agents learning from each other's interactions
3. Coordinated knowledge building
"""
import subprocess
from typing import List, Dict
from basic_agent import retrieve_memories, extract_memory


class Agent:
    """Base agent class with Cortex Memory integration"""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    def think(self, task: str) -> str:
        """Process task with memory context"""
        print(f"\n🤖 {self.name} ({self.role}) thinking...")

        # Retrieve relevant memories
        memories = retrieve_memories(task, limit=3)

        # Build context
        context = self._build_context(memories)

        # Generate response (simplified)
        response = f"[{self.name}] Based on past knowledge: {context[:100]}..."

        # Save insights
        self._save_insight(task, response)

        return response

    def _build_context(self, memories: List[Dict]) -> str:
        """Build context from memories"""
        if not memories:
            return "No prior knowledge"

        return "; ".join([m.get('summary', '')[:50] for m in memories])

    def _save_insight(self, task: str, response: str):
        """Save agent's insight to shared memory"""
        extract_memory(
            f"[{self.name}] Task: {task}\nInsight: {response}",
            memory_type="knowledge"
        )


class ResearchAgent(Agent):
    """Agent specialized in research and information gathering"""

    def __init__(self):
        super().__init__("Research Agent", "Information Gathering")

    def research(self, topic: str) -> Dict:
        """Research a topic using past knowledge"""
        print(f"\n🔍 Researching: {topic}")

        # Check existing knowledge
        memories = retrieve_memories(topic, limit=5)

        if memories:
            print(f"✅ Found {len(memories)} relevant memories")
            return {
                "topic": topic,
                "findings": [m.get('summary', '') for m in memories],
                "confidence": sum(m.get('score', 0) for m in memories) / len(memories)
            }
        else:
            print("ℹ️  No existing knowledge, need to research from scratch")
            return {
                "topic": topic,
                "findings": [],
                "confidence": 0.0
            }


class PlanningAgent(Agent):
    """Agent specialized in planning and task breakdown"""

    def __init__(self):
        super().__init__("Planning Agent", "Task Planning")

    def plan(self, goal: str) -> List[str]:
        """Create a plan based on past experiences"""
        print(f"\n📋 Planning for: {goal}")

        # Retrieve similar past experiences
        memories = retrieve_memories(f"how to {goal}", limit=3)

        # Generate plan (simplified)
        if memories:
            print(f"✅ Found {len(memories)} similar past experiences")
            steps = [f"Step based on: {m.get('summary', '')[:40]}..." for m in memories[:3]]
        else:
            print("ℹ️  No past experiences, creating new plan")
            steps = [f"Research {goal}", f"Execute {goal}", f"Validate {goal}"]

        # Save plan
        extract_memory(
            f"Plan for '{goal}': {'; '.join(steps)}",
            memory_type="task"
        )

        return steps


class ExecutionAgent(Agent):
    """Agent specialized in executing tasks"""

    def __init__(self):
        super().__init__("Execution Agent", "Task Execution")

    def execute(self, step: str) -> bool:
        """Execute a step with memory guidance"""
        print(f"\n⚙️  Executing: {step}")

        # Check for known pitfalls
        memories = retrieve_memories(f"problems with {step}", limit=2)

        if memories:
            print(f"⚠️  Found {len(memories)} known issues:")
            for mem in memories:
                print(f"   - {mem.get('summary', '')[:60]}...")

        # Execute (simplified)
        success = True  # Replace with actual execution

        # Record result
        result = "success" if success else "failed"
        extract_memory(
            f"Executed '{step}': {result}",
            memory_type="task"
        )

        return success


# Multi-agent workflow
def multi_agent_workflow(goal: str):
    """
    Demonstrate multi-agent collaboration with shared memory.
    """
    print("=" * 70)
    print(f"🎯 Multi-Agent System Goal: {goal}")
    print("=" * 70)

    # Initialize agents
    researcher = ResearchAgent()
    planner = PlanningAgent()
    executor = ExecutionAgent()

    # Step 1: Research
    research_results = researcher.research(goal)
    print(f"\n📊 Research confidence: {research_results['confidence']:.2f}")

    # Step 2: Plan
    plan = planner.plan(goal)
    print(f"\n📋 Generated plan:")
    for i, step in enumerate(plan, 1):
        print(f"   {i}. {step}")

    # Step 3: Execute
    print(f"\n⚙️  Executing plan...")
    for step in plan:
        success = executor.execute(step)
        if not success:
            print(f"❌ Failed at: {step}")
            break
    else:
        print("\n✅ All steps completed successfully!")

    # Step 4: Save final result
    extract_memory(
        f"Completed multi-agent workflow for '{goal}'. Plan: {'; '.join(plan)}",
        memory_type="knowledge"
    )


if __name__ == "__main__":
    # Example workflow
    multi_agent_workflow("set up vector database for memory system")

    print("\n" + "=" * 70)
    print("🧠 Shared Memory Updated")
    print("=" * 70)
    print("\nAll agents can now access knowledge from this workflow")
    print("in future tasks. Try querying:")
    print("  python3 scripts/retrieve_memory.py --query 'vector database setup'")
