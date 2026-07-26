"""
Multi-Agent System — CLI Entry Point

Usage:
    python main.py "Your task here"
    python main.py                    # Interactive mode

Example:
    python main.py "Build a Python function to sort a list using merge sort"
    python main.py "Research the latest trends in AI agents"
"""

import os
import sys
import uuid
import time

# ── Windows terminal encoding fix ───────────────────────────────────
# Ensures emoji and Unicode characters render properly on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

# ── Windows terminal color support ──────────────────────────────────
try:
    from colorama import init as colorama_init
    colorama_init()
except ImportError:
    pass  # Colors may not render on Windows without colorama


from config import validate_config
from graph import get_app


# ═══════════════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════════════

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🤖  MULTI-AGENT SYSTEM  v1.0                              ║
║   ─────────────────────────────────                          ║
║   Powered by LangGraph + GPT-4o                             ║
║                                                              ║
║   Agents: Planner → Researcher → Coder → Reviewer → Output  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

DIVIDER = "═" * 62


def print_header():
    """Print the startup banner."""
    print(BANNER)


def print_result(result: dict):
    """Pretty-print the final output."""
    print(f"\n{DIVIDER}")
    print("📋 FINAL OUTPUT")
    print(DIVIDER)

    final = result.get("final_output", "")
    if final:
        print(final)
    else:
        # Fallback: show last message
        messages = result.get("messages", [])
        if messages:
            print(messages[-1].content)
        else:
            print("⚠️ No output was generated.")

    print(f"\n{DIVIDER}")

    # ── Stats ───────────────────────────────────────────────────────
    revision_count = result.get("revision_count", 0)
    agent_path = []
    if result.get("plan"):
        agent_path.append("Planner")
    if result.get("research"):
        agent_path.append("Researcher")
    if result.get("code"):
        agent_path.append("Coder")
    if result.get("review"):
        agent_path.append("Reviewer")
    agent_path.append("Aggregator")

    print(f"🔄 Revisions: {revision_count}")
    print(f"🛤️  Agent path: {' → '.join(agent_path)}")
    print(DIVIDER)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════

def run_task(task: str):
    """
    Execute a task through the multi-agent pipeline.

    Args:
        task: The user's task description.
    """
    print(f"\n📝 Task: {task}")
    print(f"{DIVIDER}")
    print("⏳ Running multi-agent pipeline...\n")

    start_time = time.time()

    # Build the app
    app = get_app(use_memory=True)

    # Create a unique thread ID for memory persistence
    thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # ── Invoke the graph ────────────────────────────────────────────
    initial_state = {
        "task": task,
        "messages": [],
        "plan": "",
        "research": "",
        "code": "",
        "review": "",
        "final_output": "",
        "next_agent": "",
        "revision_count": 0,
    }

    try:
        result = app.invoke(initial_state, config=thread_config)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your OPENAI_API_KEY in .env")
        print("  2. Ensure you have internet access")
        print("  3. Try a simpler task")
        sys.exit(1)

    elapsed = time.time() - start_time
    print(f"\n⏱️  Completed in {elapsed:.1f}s")

    # ── Display results ─────────────────────────────────────────────
    print_result(result)

    return result


def interactive_mode():
    """Run in interactive loop mode."""
    print("💬 Interactive Mode — Type your tasks below.")
    print("   Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            task = input("🎯 Enter task: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye!")
            break

        if not task:
            continue
        if task.lower() in ("quit", "exit", "q"):
            print("\n👋 Goodbye!")
            break

        run_task(task)
        print()  # Spacing between tasks


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print_header()

    # ── Validate configuration ──────────────────────────────────────
    if not validate_config():
        sys.exit(1)

    # ── CLI arg mode or interactive mode ────────────────────────────
    if len(sys.argv) > 1:
        # Join all args as the task (handles unquoted multi-word input)
        task = " ".join(sys.argv[1:])
        run_task(task)
    else:
        interactive_mode()
