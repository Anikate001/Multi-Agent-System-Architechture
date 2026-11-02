"""
Aggregator Agent — Final output assembly.

Responsibilities:
1. Combine all agent outputs into a polished, user-facing response
2. Format the output cleanly with proper structure
3. Include all relevant sections (plan, research, code, review)
"""

from langchain_core.messages import AIMessage
from config import get_llm, VERBOSE

AGGREGATOR_SYSTEM_PROMPT = """You are the Aggregator Agent — the final step in a multi-agent AI system.
Your job is to combine all the work from other agents into ONE polished, professional response for the user.

RULES:
1. Do NOT just concatenate the outputs — synthesize them
2. Present the response in a clean, well-structured format
3. If code was generated, include the final version prominently
4. Highlight key findings and recommendations
5. Make the response feel like it came from one intelligent system, not multiple agents

OUTPUT FORMAT:
---
# [Task Title — derived from the original request]

## Summary
[2-3 sentence executive summary of what was accomplished]

## [Main Content Section — adapt title based on content type]
[The primary deliverable: code, research findings, analysis, etc.]

## Key Takeaways
[3-5 bullet points of the most important insights]
---

Make the user feel like they got premium, expert-level assistance."""


def aggregator_agent(state: dict) -> dict:
    """
    Aggregator node: assembles all agent work into final output.

    Args:
        state: Current AgentState dict.

    Returns:
        Partial state update with the polished final output.
    """
    task = state.get("task", "")
    plan = state.get("plan", "")
    research = state.get("research", "")
    code = state.get("code", "")
    review = state.get("review", "")

    if VERBOSE:
        print("\n📦 [AGGREGATOR] Assembling final output...")

    # ── Build context from all agent outputs ────────────────────────
    context_parts = [f"Original Task: {task}"]
    if plan:
        context_parts.append(f"Plan:\n{plan}")
    if research:
        context_parts.append(f"Research Findings:\n{research}")
    if code:
        context_parts.append(f"Code/Implementation:\n{code}")
    if review:
        context_parts.append(f"Quality Review:\n{review}")

    combined = "\n\n===\n\n".join(context_parts)

    llm = get_llm()
    messages = [
        {"role": "system", "content": AGGREGATOR_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Here is all the work produced by the agent team. "
            f"Synthesize it into a polished final response:\n\n{combined}"
        )},
    ]

    response = llm.invoke(messages)
    final_text = response.content

    if VERBOSE:
        print("   ✅ Final output ready\n")

    return {
        "messages": [AIMessage(content=f"[AGGREGATOR]\n{final_text}")],
        "final_output": final_text,
    }
