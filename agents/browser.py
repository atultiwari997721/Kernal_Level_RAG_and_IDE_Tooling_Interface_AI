"""Browser and Media Specialist Agent for KritiAI."""
from typing import Any, Dict
from agents.base import AgentAction, BaseAgent
from security.policies.models import RiskLevel


class BrowserAgent(BaseAgent):
    """Specialized agent for web browsing, media playback (YouTube), and online automation."""
    name = "BrowserAgent"
    description = "Navigates websites, plays songs on YouTube, and performs web searches."
    capabilities = ["play_youtube", "open_url", "search_web"]
    allowed_tools = ["browser"]
    risk_level = RiskLevel.LOW

    def plan_step(self, objective: str, context: Dict[str, Any]) -> AgentAction:
        obj_lower = objective.lower()
        query = context.get("query") or objective

        if "youtube" in obj_lower or "play" in obj_lower or "song" in obj_lower:
            return AgentAction(
                tool_name="browser",
                parameters={"operation": "play_youtube", "query": query},
                thought=f"Navigating to YouTube to play: '{query}'",
                expected_result=f"YouTube opened and playing '{query}'"
            )
        elif "search" in obj_lower:
            return AgentAction(
                tool_name="browser",
                parameters={"operation": "search_web", "query": query},
                thought=f"Performing web search for: '{query}'",
                expected_result=f"Web search results displayed for '{query}'"
            )
        else:
            url = context.get("url") or "https://www.google.com"
            return AgentAction(
                tool_name="browser",
                parameters={"operation": "open_url", "url": url},
                thought=f"Opening web page '{url}'",
                expected_result=f"Web page '{url}' loaded"
            )
