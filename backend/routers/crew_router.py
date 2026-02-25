"""Crew run endpoints and WebSocket streaming."""

import asyncio
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger("crew_router")

from backend.config import MOCK_MODE, OUTPUT_DIR
from backend.crew.run_manager import run_manager
from backend.crew.mock_runner import run_mock_crew

router = APIRouter()
ws_router = APIRouter()


class CrewRunRequest(BaseModel):
    topic: str


@router.post("/run")
async def start_crew_run(request: CrewRunRequest):
    """Kick off a crew run. Returns a run_id for WebSocket subscription."""
    run_id = str(uuid4())[:8]
    run = run_manager.create_run(run_id, request.topic)

    if MOCK_MODE:
        asyncio.create_task(run_mock_crew(run))
    else:
        # Real crew run — will be implemented in Phase 4
        asyncio.create_task(_run_real_crew(run))

    return {"run_id": run_id, "status": "started"}


@router.get("/status/{run_id}")
async def crew_status(run_id: str):
    """Get current state of a crew run."""
    run = run_manager.get_run(run_id)
    if not run:
        return {"error": "Run not found", "run_id": run_id}

    return {
        "run_id": run.run_id,
        "topic": run.topic,
        "status": run.status,
        "elapsed_seconds": run.elapsed_seconds,
        "events_count": len(run.bridge.events),
        "report_path": run.report_path,
        "charts": run.charts,
        "error": run.error,
    }


@router.get("/report/{run_id}")
async def crew_report(run_id: str):
    """Return the completed markdown report content."""
    run = run_manager.get_run(run_id)
    if not run:
        return {"error": "Run not found"}
    if not run.report_path:
        return {"error": "Report not ready", "status": run.status}

    # report_path is like "/output/report.md" — resolve to filesystem
    filename = run.report_path.replace("/output/", "")
    filepath = OUTPUT_DIR / filename
    if not filepath.exists():
        return {"error": "Report file not found"}

    return {
        "run_id": run_id,
        "report": filepath.read_text(encoding="utf-8"),
        "charts": run.charts,
    }


@router.get("/runs")
async def list_runs():
    """List all crew runs."""
    return {"runs": run_manager.list_runs()}


@router.get("/events/{run_id}")
async def crew_events(run_id: str):
    """Debug: return all events for a run."""
    run = run_manager.get_run(run_id)
    if not run:
        return {"error": "Run not found"}
    return {"events": run.bridge.events}


@ws_router.websocket("/stream/{run_id}")
async def crew_stream(websocket: WebSocket, run_id: str):
    """Real-time event stream for a crew run."""
    await websocket.accept()

    run = run_manager.get_run(run_id)
    if not run:
        await websocket.send_json({"type": "error", "message": "Run not found"})
        await websocket.close()
        return

    try:
        # Stream all events (past and future) using index-based consumer
        # This handles both replay and live streaming in one pass
        async for event in run.bridge.consume_from(0):
            await websocket.send_json(event)

        # All events delivered — wait for the client to close
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass


async def _run_real_crew(run):
    """Execute a real CrewAI crew run with Ollama models."""
    from datetime import datetime, timezone
    from backend.crew.crew import build_crew
    from backend.config import CHARTS_DIR

    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    bridge = run.bridge

    bridge.push_event({
        "type": "agent_start",
        "agent": "manager",
        "role": "Senior Research Director",
        "model": "gemma3:27b",
        "vm": "orchestrator",
        "task_summary": f"Orchestrating research on: {run.topic}",
    })

    # Snapshot existing charts BEFORE the run so we only report new ones
    existing_charts = set(f.name for f in CHARTS_DIR.glob("*.png"))

    try:
        crew = build_crew(
            topic=run.topic,
            bridge=bridge,
        )

        # CrewAI runs synchronously — must run in a thread
        result = await asyncio.to_thread(crew.kickoff)

        run.completed_at = datetime.now(timezone.utc)
        elapsed = run.elapsed_seconds or 0

        # Collect only NEW chart paths created during this run
        run.charts = [
            f"/output/charts/{f.name}"
            for f in CHARTS_DIR.glob("*.png")
            if f.name not in existing_charts
        ]

        # Extract the best report content from multiple sources.
        # The writer LLM often botches the FileTool call (e.g., saving
        # the filename as content), so we check multiple sources and
        # pick the longest/best one.
        from backend.config import OUTPUT_DIR
        report_file = OUTPUT_DIR / "report.md"

        candidates = []

        # Source 1: File saved by FileTool (if it looks like real content)
        if report_file.exists():
            file_content = report_file.read_text(encoding="utf-8").strip()
            if len(file_content) > 200:
                candidates.append(file_content)

        # Source 2: Crew result
        raw_result = str(result).strip()
        if len(raw_result) > 200:
            candidates.append(raw_result)

        # Source 3: Longest writer agent_output from the event stream
        writer_outputs = [
            e.get("content", "")
            for e in bridge.events
            if e.get("agent") == "writer" and e.get("type") == "agent_output"
        ]
        if writer_outputs:
            longest = max(writer_outputs, key=len)
            if len(longest) > 200:
                candidates.append(longest)

        # Pick the longest candidate — that's almost certainly the real report
        if candidates:
            best = max(candidates, key=len)
            report_content = _clean_report(best, chart_files=run.charts)
            report_file.write_text(report_content, encoding="utf-8")
            run.report_path = "/output/report.md"
        else:
            logger.warning("No report content found from any source")

        # Emit chart_created events for each new chart
        for chart_path in run.charts:
            bridge.push_event({
                "type": "chart_created",
                "agent": "visualizer",
                "chart_title": chart_path.split("/")[-1].replace(".png", "").replace("_", " ").title(),
                "path": chart_path,
            })

        bridge.push_event({
            "type": "crew_complete",
            "total_seconds": round(elapsed, 1),
            "report_path": run.report_path,
            "charts": run.charts,
        })
        run.status = "completed"

    except Exception as e:
        run.status = "error"
        run.error = str(e)
        bridge.push_event({
            "type": "error",
            "agent": "system",
            "message": f"Crew execution failed: {e}",
            "recoverable": False,
        })

    finally:
        bridge.mark_complete()


def _clean_report(content: str, chart_files: list[str] = None) -> str:
    """Strip LLM artifacts from report content and fix image references."""
    import re
    content = content.strip()

    # Remove "Thought: ..." preamble before the actual markdown
    # The real report starts at the first markdown heading
    thought_match = re.match(r'^Thought:.*?(?=^#)', content, flags=re.DOTALL | re.MULTILINE)
    if thought_match:
        content = content[thought_match.end():].strip()

    # Also handle "Thought: ..." followed by ```markdown
    thought_match2 = re.match(r'^Thought:.*?(?=```)', content, flags=re.DOTALL)
    if thought_match2:
        content = content[thought_match2.end():].strip()

    # Remove ```markdown ... ``` wrapping
    if content.startswith("```markdown"):
        content = content[len("```markdown"):].strip()
    elif content.startswith("```md"):
        content = content[len("```md"):].strip()
    elif content.startswith("```"):
        content = content[3:].strip()
    if content.endswith("```"):
        content = content[:-3].strip()

    # Fix image references to match actual chart files on disk
    if chart_files:
        content = _fix_chart_refs(content, chart_files)

    return content


def _fix_chart_refs(content: str, chart_files: list[str]) -> str:
    """Fix markdown image references to point to actual chart files.

    The writer LLM often gets paths wrong — wrong extension (.json instead of .png),
    wrong prefix, missing path, etc. We match by fuzzy filename stem comparison.
    """
    import re
    from pathlib import Path

    # Build a lookup from stem fragments to actual paths
    # e.g. "cdn_market_share_2023" -> "/output/charts/cdn_market_share_2023.png"
    stem_to_path = {}
    for chart_path in chart_files:
        stem = Path(chart_path).stem  # e.g. "cdn_market_share_2023"
        stem_to_path[stem] = chart_path
        # Also index without common suffixes the model adds
        stem_to_path[stem.lower()] = chart_path

    def replace_image(match):
        full_match = match.group(0)
        alt = match.group(1)
        ref_path = match.group(2)

        # Extract the stem from whatever the writer put
        ref_stem = Path(ref_path).stem  # strips .json, .png, etc.

        # Try exact match
        if ref_stem in stem_to_path:
            return f"![{alt}]({stem_to_path[ref_stem]})"
        if ref_stem.lower() in stem_to_path:
            return f"![{alt}]({stem_to_path[ref_stem.lower()]})"

        # Try fuzzy: find the chart whose stem contains or is contained by ref_stem
        for stem, path in stem_to_path.items():
            if stem in ref_stem.lower() or ref_stem.lower() in stem:
                return f"![{alt}]({path})"

        # No match — leave as-is but fix to .png extension
        fixed = re.sub(r'\.\w+$', '.png', ref_path)
        if not fixed.endswith('.png'):
            fixed += '.png'
        return f"![{alt}]({fixed})"

    # Match markdown image syntax: ![alt](path)
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, content)
    return content
