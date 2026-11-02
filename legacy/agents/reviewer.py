"""
Reviewer Agent — Quality control and critical analysis.

Responsibilities:
1. Review the work product (code, research, or direct answers)
2. Check for errors, gaps, and improvements
3. Decide: PASS (send to aggregator) or NEEDS_REVISION (loop back)
"""

from langchain_core.messages import AIMessage
from config import get_llm, MAX_REVISIONS, VERBOSE

REVIEWER_SYSTEM_PROMPT = """You are a Reviewer/Critic Agent in a multi-agent AI system.
Your job is to critically evaluate the work produced by other agents.

REVIEW CHECKLIST:
1. ✅ Correctness — Is the output factually/logically correct?
2. ✅ Completeness — Does it fully address the original task?
3. ✅ Quality — Is it well-structured, clear, and professional?
4. ✅ Code (if applicable) — Does it follow best practices? Any bugs?

VERDICT OPTIONS:
- **PASS** — Work meets quality standards. Ready for final output.
- **NEEDS_REVISION** — Work has issues that need fixing. List specific problems.

OUTPUT FORMAT:
---
## Review Summary
[2-3 sentence overall assessment]

## Issues Found
[Numbered list of specific issues, or "None" if work is acceptable]

## Verdict
[EXACTLY one of: PASS | NEEDS_REVISION]

## Revision Instructions (if NEEDS_REVISION)
[Specific, actionable instructions for the agent to fix the issues]
---

Be fair but thorough. Don't pass low-quality work. Don't nitpick perfect work."""


def reviewer_agent(state: dict) -> dict:
    """
    Reviewer node: evaluates work and decides pass/fail.

    Args:
        state: Current AgentState dict.

    Returns:
        Partial state update with review feedback and routing decision.
    """
    task = state.get("task", "")
    plan = state.get("plan", "")
    research = state.get("research", "")
    code = state.get("code", "")
    revision_count = state.get("revision_count", 0)

    if VERBOSE:
        print("\n🔎 [REVIEWER] Evaluating work product...")

    # ── Collect all work product ────────────────────────────────────
    work_sections = [f"Original Task: {task}"]
    if plan:
        work_sections.append(f"Plan:\n{plan}")
    if research:
        work_sections.append(f"Research:\n{research}")
    if code:
        work_sections.append(f"Code/Output:\n{code}")

    work_product = "\n\n---\n\n".join(work_sections)

    # ── Force PASS if max revisions reached ─────────────────────────
    force_pass = revision_count >= MAX_REVISIONS
    extra_instruction = ""
    if force_pass:
        extra_instruction = (
            "\n\n⚠️ NOTE: Maximum revision limit reached. "
            "You MUST give a PASS verdict regardless of minor issues. "
            "Focus your review on summarizing what was accomplished."
        )

    llm = get_llm()
    messages = [
        {"role": "system", "content": REVIEWER_SYSTEM_PROMPT + extra_instruction},
        {"role": "user", "content": f"Please review the following work product:\n\n{work_product}"},
    ]

    response = llm.invoke(messages)
    review_text = response.content

    # ── Parse verdict ───────────────────────────────────────────────
    verdict = "PASS"  # Default to pass
    review_lower = review_text.lower()

    if "## verdict" in review_lower:
        verdict_section = review_text.split("## Verdict")[-1].split("##")[0].strip()
        verdict_line = verdict_section.strip().split("\n")[0].strip().upper()

        if "NEEDS_REVISION" in verdict_line and not force_pass:
            verdict = "NEEDS_REVISION"
        else:
            verdict = "PASS"

    # ── Determine routing ───────────────────────────────────────────
    if verdict == "NEEDS_REVISION":
        next_agent = "coder" if code else "researcher"
        new_revision_count = revision_count + 1
        if VERBOSE:
            print(f"   ⚠️  NEEDS_REVISION (attempt {new_revision_count}/{MAX_REVISIONS})")
    else:
        next_agent = "aggregator"
        new_revision_count = revision_count
        if VERBOSE:
            print("   ✅ PASS — Sending to aggregator")

    return {
        "messages": [AIMessage(content=f"[REVIEWER]\n{review_text}")],
        "review": review_text,
        "next_agent": next_agent,
        "revision_count": new_revision_count,
    }
