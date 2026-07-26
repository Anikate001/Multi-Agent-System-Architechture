from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import time
import structlog
from pydantic import BaseModel

from schemas.agents import AgentRole, AgentAction
from services.llm_service import LLMService
from memory.state_manager import StateManager

logger = structlog.get_logger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all specialized research agents."""
    
    def __init__(
        self, 
        role: AgentRole, 
        llm_service: LLMService, 
        tools: dict, 
        memory: StateManager
    ):
        self.role = role
        self.llm = llm_service
        self.tools = tools
        self.memory = memory
        self._token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        
    @property
    def token_usage(self) -> Dict[str, int]:
        return self._token_usage

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's primary function given the current state."""
        pass

    async def log_action(
        self, 
        action: str, 
        input_data: Any, 
        output_data: Any, 
        tokens: int, 
        latency_ms: int,
        success: bool = True
    ) -> AgentAction:
        """Log an action performed by the agent."""
        agent_action = AgentAction(
            agent=self.role,
            action=action,
            input_data=input_data if isinstance(input_data, dict) else {"data": str(input_data)},
            output_data=output_data if isinstance(output_data, dict) else {"data": str(output_data)},
            tokens_used=tokens,
            latency_ms=latency_ms,
            timestamp=time.time(),
            success=success
        )
        
        if success:
            logger.info("agent_action_success", agent=self.role.value, action=action, tokens=tokens, latency_ms=latency_ms)
        else:
            logger.error("agent_action_failed", agent=self.role.value, action=action, latency_ms=latency_ms)
            
        return agent_action
        
    async def _safe_execute(self, func, *args, **kwargs):
        """Wrapper for safe execution of agent tasks with error handling."""
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            latency = int((time.time() - start_time) * 1000)
            return result, latency, True
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.exception("agent_execution_error", agent=self.role.value, error=str(e))
            return str(e), latency, False
