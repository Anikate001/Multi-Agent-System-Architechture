from typing import TypedDict, Optional, List, Dict, Any
from typing_extensions import Annotated
import operator

# Reducer functions to handle state updates in LangGraph
def update_list(existing: list, new: list) -> list:
    """Append new items to existing list."""
    if existing is None:
        return new if new is not None else []
    if new is None:
        return existing
    return existing + new

def update_dict(existing: dict, new: dict) -> dict:
    """Merge new dict into existing dict."""
    if existing is None:
        return new if new is not None else {}
    if new is None:
        return existing
    res = existing.copy()
    res.update(new)
    return res

def overwrite(existing: Any, new: Any) -> Any:
    """Simply overwrite the existing value."""
    return new if new is not None else existing

class ResearchState(TypedDict):
    """
    The state dictionary that is passed between nodes in the LangGraph workflow.
    Uses Annotated with reducers to specify how state updates should be handled.
    """
    task_id: str
    query: str
    depth: str
    
    # Core artifacts
    plan: Annotated[Optional[Dict[str, Any]], overwrite]
    findings: Annotated[List[Dict[str, Any]], update_list]
    analysis: Annotated[Optional[Dict[str, Any]], overwrite]
    draft_report: Annotated[Optional[Dict[str, Any]], overwrite]
    review: Annotated[Optional[Dict[str, Any]], overwrite]
    
    # Workflow control
    revision_count: Annotated[int, operator.add]
    approved: Annotated[bool, overwrite]
    human_approved: Annotated[Optional[bool], overwrite]
    require_human_approval: bool
    
    # Metadata & Tracking
    agent_actions: Annotated[List[Dict[str, Any]], update_list]
    token_usage: Annotated[Dict[str, int], update_dict]
    errors: Annotated[List[str], update_list]
    status: Annotated[str, overwrite]
    current_agent: Annotated[str, overwrite]
