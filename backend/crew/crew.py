"""CrewAI Crew definition — hierarchical process with manager + specialists."""

from crewai import Crew, Process

from backend.config import OUTPUT_DIR
from backend.crew.agents import (
    build_manager,
    build_researcher,
    build_analyst,
    build_visualizer,
    build_writer,
)
from backend.crew.tasks import build_tasks
from backend.crew.tools import chart_tool, file_tool


# Explicit agent info for each task in pipeline order
TASK_AGENTS = [
    ("researcher", "Market Research Specialist", "qwen2.5:14b", "specialist"),
    ("analyst", "Data Analyst", "qwen2.5:14b", "specialist"),
    ("visualizer", "Data Visualization Specialist", "qwen2.5:14b", "specialist"),
    ("writer", "Report Writer", "qwen2.5:14b", "specialist"),
]


def build_crew(topic: str, bridge=None) -> Crew:
    """Build a fully configured crew for the given research topic."""

    # Build agents
    manager = build_manager()
    researcher = build_researcher()
    analyst = build_analyst()
    visualizer = build_visualizer(tools=[chart_tool])
    writer = build_writer(tools=[file_tool])

    # Build tasks (always in this order: research → analysis → visualization → writing)
    tasks = build_tasks(
        topic=topic,
        researcher=researcher,
        analyst=analyst,
        visualizer=visualizer,
        writer=writer,
    )

    # In hierarchical mode, the manager's executor handles all tasks.
    # We track which task index is active and attribute events accordingly.
    if bridge:
        task_index = [0]  # Mutable container for closure

        manager.step_callback = bridge.step_callback

        # Set the first agent as current
        bridge.set_current_agent(*TASK_AGENTS[0])

        def _task_callback(task_output):
            current_idx = task_index[0]
            agent_key, agent_role, _, _ = TASK_AGENTS[current_idx]

            # Emit agent_complete for the finishing agent
            bridge.push_event({
                "type": "agent_complete",
                "agent": agent_key,
                "role": agent_role,
            })

            # Advance to next task
            next_idx = current_idx + 1
            if next_idx < len(TASK_AGENTS):
                # Manager delegates — show the handoff
                next_key, next_role, next_model, next_vm = TASK_AGENTS[next_idx]
                bridge.push_event({
                    "type": "delegation",
                    "from": "manager",
                    "to": next_key,
                    "instruction": f"Delegating to {next_role}",
                })
                bridge.set_current_agent(next_key, next_role, next_model, next_vm)
                task_index[0] = next_idx

        crew_kwargs_extra = {"task_callback": _task_callback}
    else:
        crew_kwargs_extra = {}

    # Assemble crew
    log_path = str(OUTPUT_DIR / "crew_log.txt")
    crew_kwargs = dict(
        agents=[researcher, analyst, visualizer, writer],
        tasks=tasks,
        manager_agent=manager,
        process=Process.hierarchical,
        verbose=True,
        output_log_file=log_path,
        **crew_kwargs_extra,
    )

    return Crew(**crew_kwargs)
