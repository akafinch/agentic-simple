"""CrewAI step_callback → WebSocket event bridge."""

import asyncio
import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger("crew_callbacks")


def _clean_content(content: str) -> str:
    """Clean up raw CrewAI output for display in the UI."""
    if not content:
        return ""

    # Strip ToolResult(result='...', result_as_answer=...) wrappers
    # Match: ToolResult(result='...' followed by optional kwargs and closing paren
    m = re.match(r"ToolResult\(result=['\"](.+)", content, flags=re.DOTALL)
    if m:
        inner = m.group(1)
        # Remove trailing ', result_as_answer=...) or similar
        inner = re.sub(r"['\"],\s*result_as_answer=\w+\)\s*$", "", inner, flags=re.DOTALL)
        # Also handle simple closing
        inner = re.sub(r"['\"]\)\s*$", "", inner)
        content = inner.strip()

    # Strip AgentFinish(...) wrappers
    m = re.match(r"AgentFinish\(thought=['\"].*?['\"],\s*output=['\"](.+)", content, flags=re.DOTALL)
    if m:
        inner = m.group(1)
        inner = re.sub(r"['\"]\)\s*$", "", inner)
        content = inner.strip()

    # Strip "### Assistant:" prefix that Gemma sometimes adds
    content = re.sub(r"^###?\s*Assistant:\s*", "", content, flags=re.IGNORECASE)

    # Truncate for live stream display
    if len(content) > 1500:
        content = content[:1500] + "... [truncated]"

    return content.strip()


class CrewEventBridge:
    """Bridges CrewAI's synchronous callbacks to async WebSocket consumers."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.events: list[dict] = []
        self._complete = False
        self._notify: asyncio.Event = asyncio.Event()
        self._current_agent = ("manager", "Senior Research Director")

    def push_event(self, event: dict):
        """Push an event (from any context — sync or async)."""
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
        event["run_id"] = self.run_id
        self.events.append(event)
        self._notify.set()

    def step_callback(self, step_output):
        """Called by CrewAI on each agent step. Runs in a sync thread.

        In hierarchical mode, this fires on the manager's executor for all work.
        We use _current_agent (set by task_callback) to attribute correctly.
        """
        from crewai.agents.parser import AgentAction, AgentFinish

        agent_key, agent_role = self._current_agent

        if isinstance(step_output, AgentFinish):
            output = step_output.output
            content = _clean_content(str(output) if output else step_output.text)
            if not content:
                return
            self.push_event({
                "type": "agent_output",
                "agent": agent_key,
                "role": agent_role,
                "content": content,
            })
        elif isinstance(step_output, AgentAction):
            tool_name = step_output.tool
            self.push_event({
                "type": "tool_use",
                "agent": agent_key,
                "role": agent_role,
                "tool": tool_name,
                "tool_input": (step_output.tool_input or "")[:500],
                "content": f"Using tool: {tool_name}",
            })
        else:
            content = _clean_content(str(step_output))
            if content:
                self.push_event({
                    "type": "agent_output",
                    "agent": agent_key,
                    "role": agent_role,
                    "content": content,
                })

    def set_current_agent(self, agent_key: str, agent_role: str, model: str, vm: str):
        """Update the current agent and emit an agent_start event."""
        self._current_agent = (agent_key, agent_role)
        self.push_event({
            "type": "agent_start",
            "agent": agent_key,
            "role": agent_role,
            "model": model,
            "vm": vm,
            "task_summary": f"{agent_role} is working...",
        })

    def mark_complete(self):
        """Signal that no more events will be produced."""
        self._complete = True
        self._notify.set()

    @property
    def is_complete(self) -> bool:
        return self._complete

    async def consume_from(self, start_index: int = 0):
        """Async generator that yields events starting from start_index.

        Uses an asyncio.Event for notification instead of a queue,
        so multiple consumers and late-joiners work correctly.
        """
        idx = start_index
        while True:
            # Yield any events we haven't seen yet
            while idx < len(self.events):
                yield self.events[idx]
                idx += 1

            # If complete and we've yielded everything, stop
            if self._complete and idx >= len(self.events):
                break

            # Wait for new events (with timeout to check completion)
            self._notify.clear()
            try:
                await asyncio.wait_for(self._notify.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
