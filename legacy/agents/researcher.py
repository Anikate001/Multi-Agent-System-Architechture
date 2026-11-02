"""
Researcher Agent — Gathers external information for the team.

Responsibilities:
1. Extract key search queries from the plan
2. Perform web searches using available tools
3. Synthesize findings into structured research notes
"""

from langchain_core.messages import AIMessage
from config import get_llm, VERBOSE
from tools import web_search

RESEARCHER_SYSTEM_PROMPT = """You are a Research Agent in a multi-agent AI system.
You have access to web search results. Your job is to:

1. Identify the key information needed based on the plan
2. Analyze the search results provided
3. Produce a clear, well-organized research summary

OUTPUT FORMAT:
---
## Key Findings
[Bullet points of the most important facts/data]

## Sources & Context
[Relevant details with source attribution where possible]

## Recommendations for Next Steps
[How this research should inform the next agent's work]
---

Be thorough but concise. Focus on actionable information."""


def researcher_agent(state: dict) -> dict:
    """
    Researcher node: searches the web and synthesizes findings.

    Args:
        state: Current AgentState dict.

    Returns:
        Partial state update with research findings.
    """
    task = state.get("task", "")
    plan = state.get("plan", "")

    if VERBOSE:
        print("\n🔍 [RESEARCHER] Gathering information...")

    # ── Generate smart search queries from the plan ─────────────────
    llm = get_llm()
    query_prompt = [
        {"role": "system", "content": "Extract 1-3 focused web search queries from this task and plan. Return ONLY the queries, one per line."},
        {"role": "user", "content": f"Task: {task}\n\nPlan:\n{plan}"},
    ]
    query_response = llm.invoke(query_prompt)
    queries = [q.strip() for q in query_response.content.strip().split("\n") if q.strip()]

    # Limit to 3 queries max
    queries = queries[:3]

    if VERBOSE:
        for q in queries:
            print(f"   🔎 Searching: {q}")

    # ── Perform searches ────────────────────────────────────────────
    all_results = []
    for query in queries:
        result = web_search(query)
        all_results.append(f"### Query: {query}\n{result}")

    combined_results = "\n\n".join(all_results)

    # ── Synthesize findings ─────────────────────────────────────────
    synthesis_prompt = [
        {"role": "system", "content": RESEARCHER_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Task: {task}\n\n"
            f"Plan:\n{plan}\n\n"
            f"Search Results:\n{combined_results}"
        )},
    ]

    synthesis = llm.invoke(synthesis_prompt)
    research_text = synthesis.content

    if VERBOSE:
        print("   ✅ Research complete")

    return {
        "messages": [AIMessage(content=f"[RESEARCHER]\n{research_text}")],
        "research": research_text,
    }
