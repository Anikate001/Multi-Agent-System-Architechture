"""
Planner Agent — The orchestrator of the multi-agent system.

Responsibilities:
1. Analyze the user's task
2. Create a structured execution plan
3. Decide which agents are needed (routing)
"""

from langchain_core.messages import AIMessage
from config import get_llm, VERBOSE

PLANNER_SYSTEM_PROMPT = """You are a Planning Agent in a multi-agent AI system.
Your job is to analyze a user's task and create a clear, actionable plan.

You MUST also decide which specialist agents are needed:
- "researcher" → if the task requires gathering external information, facts, or data
- "coder" → if the task requires writing, debugging, or explaining code
- "researcher_then_coder" → if the task needs research FIRST, then code generation
- "direct_review" → if the task is simple enough to answer directly (no specialist needed)

OUTPUT FORMAT (you MUST follow this exactly):
---
## Plan
[Write 3-5 clear, numbered steps for completing this task]

## Route
[Write EXACTLY one of: researcher | coder | researcher_then_coder | direct_review]

## Reasoning
[1-2 sentences explaining why you chose this route]
---

Be precise. Be decisive. Do not hedge."""


def planner_agent(state: dict) -> dict:
    """
    Planner node: analyzes the task and decides the execution route.

    Args:
        state: Current AgentState dict.

    Returns:
        Partial state update with plan and routing decision.
    """
    task = state.get("task", "")

    if VERBOSE:
        print("\n🧠 [PLANNER] Analyzing task and creating plan...")

    llm = get_llm()
    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {task}"},
    ]

    response = llm.invoke(messages)
    plan_text = response.content

    # ── Parse the route from the plan ───────────────────────────────
    route = "direct_review"  # Default fallback
    plan_lower = plan_text.lower()

    if "## route" in plan_lower:
        # Extract the route line
        route_section = plan_text.split("## Route")[-1].split("##")[0].strip()
        route_line = route_section.strip().split("\n")[0].strip().lower()

        if "researcher_then_coder" in route_line:
            route = "researcher_then_coder"
        elif "researcher" in route_line:
            route = "researcher"
        elif "coder" in route_line:
            route = "coder"
        elif "direct_review" in route_line:
            route = "direct_review"

    if VERBOSE:
        print(f"   📋 Plan created → Route: {route}")

    return {
        "messages": [AIMessage(content=f"[PLANNER]\n{plan_text}")],
        "plan": plan_text,
        "next_agent": route,
    }
