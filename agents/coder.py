"""
Coder Agent — Generates and refines code solutions.

Responsibilities:
1. Write clean, well-documented code based on plan + research
2. Handle revision requests from the Reviewer
3. Include error handling and docstrings
"""

from langchain_core.messages import AIMessage
from config import get_llm, VERBOSE

CODER_SYSTEM_PROMPT = """You are a Coder Agent in a multi-agent AI system.
Your job is to write high-quality, production-ready code.

RULES:
1. Write clean, well-structured code with proper docstrings
2. Include error handling (try/except where appropriate)
3. Add helpful inline comments for complex logic
4. If research data is provided, incorporate those findings
5. If review feedback is provided, address ALL issues raised

OUTPUT FORMAT:
---
## Implementation
[Explain what you're building and key design decisions]

## Code
```python
[Your complete, runnable code here]
```

## Usage
[How to run/use this code — include example commands or function calls]
---

Write code that works on the first run. No placeholders. No TODOs."""


REVISION_PROMPT = """You are a Coder Agent receiving revision feedback from a Reviewer.

PREVIOUS CODE:
{previous_code}

REVIEWER FEEDBACK:
{review_feedback}

Fix ALL issues raised by the reviewer. Return the COMPLETE updated code (not just patches).
Follow the same output format as before."""


def coder_agent(state: dict) -> dict:
    """
    Coder node: generates or revises code based on context.

    Args:
        state: Current AgentState dict.

    Returns:
        Partial state update with generated code.
    """
    task = state.get("task", "")
    plan = state.get("plan", "")
    research = state.get("research", "")
    previous_code = state.get("code", "")
    review_feedback = state.get("review", "")
    revision_count = state.get("revision_count", 0)

    llm = get_llm()

    # ── Revision mode (feedback loop) ───────────────────────────────
    if previous_code and review_feedback and revision_count > 0:
        if VERBOSE:
            print(f"\n💻 [CODER] Revising code (revision #{revision_count})...")

        messages = [
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": REVISION_PROMPT.format(
                previous_code=previous_code,
                review_feedback=review_feedback,
            )},
        ]
    else:
        # ── First-time code generation ──────────────────────────────
        if VERBOSE:
            print("\n💻 [CODER] Writing code...")

        context_parts = [f"Task: {task}"]
        if plan:
            context_parts.append(f"Plan:\n{plan}")
        if research:
            context_parts.append(f"Research Findings:\n{research}")

        messages = [
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": "\n\n".join(context_parts)},
        ]

    response = llm.invoke(messages)
    code_text = response.content

    if VERBOSE:
        print("   ✅ Code generated")

    return {
        "messages": [AIMessage(content=f"[CODER]\n{code_text}")],
        "code": code_text,
    }
