from typing import Dict, Any
import structlog

from agents.base import BaseAgent
from schemas.agents import AgentRole

logger = structlog.get_logger(__name__)

class ToolAgent(BaseAgent):
    """Executes specific tools requested by other agents."""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # This is a simplified tool agent. In a more complex setup, it would
        # receive a specific tool call request (e.g., from an LLM function calling output)
        # and route it to the appropriate tool implementation.
        
        tool_request = state.get("tool_request", {})
        tool_name = tool_request.get("name")
        tool_args = tool_request.get("args", {})
        
        logger.info("tool_agent_started", tool=tool_name)
        
        if not tool_name or tool_name not in self.tools:
            return {"errors": [f"Tool '{tool_name}' not found"], "status": "TOOL_FAILED"}
            
        tool = self.tools[tool_name]
        
        async def execute_tool():
            # Simplistic dynamic call - assumes tools have an `execute` or similar main method
            # In a real implementation, you'd map standard interfaces.
            if hasattr(tool, 'execute') and callable(getattr(tool, 'execute')):
                return await tool.execute(**tool_args)
            elif hasattr(tool, 'search') and callable(getattr(tool, 'search')):
                return await tool.search(**tool_args)
            else:
                 raise ValueError(f"Tool {tool_name} does not have a recognized execution method.")

        result, latency, success = await self._safe_execute(execute_tool)
        
        if success:
            await self.log_action(
                action=f"execute_{tool_name}",
                input_data=tool_args,
                output_data={"result_type": str(type(result))},
                tokens=0, # Tool execution might not use LLM tokens
                latency_ms=latency,
                success=True
            )
            return {"tool_result": result, "status": "TOOL_COMPLETED", "current_agent": self.role.value}
        else:
            await self.log_action(
                action=f"execute_{tool_name}",
                input_data=tool_args,
                output_data={"error": str(result)},
                tokens=0,
                latency_ms=latency,
                success=False
            )
            return {"errors": [str(result)], "status": "TOOL_FAILED", "current_agent": self.role.value}
