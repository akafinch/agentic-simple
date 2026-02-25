"""CrewAI tool wrappers for chart generation and file saving."""

import json
import logging
from typing import Any
from crewai.tools import tool

from backend.tools.chart_tool import generate_chart
from backend.tools.file_tool import save_report

logger = logging.getLogger("crew_tools")


@tool("ChartTool")
def chart_tool(chart_data: str) -> str:
    """Generate a professional chart image.

    Pass a JSON string with these fields:
    {
        "chart_type": "bar",
        "title": "Chart Title",
        "labels": ["A", "B", "C"],
        "values": [10, 20, 30],
        "unit": "%",
        "filename": "my_chart"
    }

    chart_type options: bar, horizontal_bar, pie, line
    Returns the file path of the generated chart image.
    """
    try:
        data = _parse_chart_input(chart_data)
        path = generate_chart(
            chart_type=data.get("chart_type", "bar"),
            title=data.get("title", "Chart"),
            labels=[str(l) for l in data.get("labels", [])],
            values=[float(v) for v in data.get("values", [])],
            unit=data.get("unit", ""),
            filename=data.get("filename", "chart"),
        )
        return f"Chart saved to: {path}"
    except Exception as e:
        logger.error(f"ChartTool error: {e}")
        return f"Error generating chart: {e}"


def _parse_chart_input(raw: Any) -> dict:
    """Robustly parse chart input from various LLM output formats."""
    # Already a dict with the right keys
    if isinstance(raw, dict):
        if "chart_type" in raw:
            return raw
        # Model passed the schema definition instead of values
        if "properties" in raw:
            logger.warning("ChartTool received schema instead of data, attempting extraction")
            props = raw["properties"]
            # Try to extract default/example values from schema
            extracted = {}
            for key, spec in props.items():
                if isinstance(spec, dict):
                    extracted[key] = spec.get("default", spec.get("description", ""))
            return extracted
        return raw

    # JSON string
    if isinstance(raw, str):
        # Try direct JSON parse
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in the string (model may have wrapped it in text)
        import re
        json_match = re.search(r'\{[^{}]*"chart_type"[^{}]*\}', raw, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try to find a JSON block with nested arrays
        json_match = re.search(r'\{.*?"labels"\s*:\s*\[.*?\].*?\}', raw, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not parse chart input: {str(raw)[:200]}")


@tool("FileTool")
def file_tool(filename: str, content: str) -> str:
    """Save content to a file in the output directory. Arguments:
    - filename: Name for the file (without path)
    - content: The text content to save

    Returns the path where the file was saved.
    """
    path = save_report(filename, content)
    return f"Report saved to: {path}"
