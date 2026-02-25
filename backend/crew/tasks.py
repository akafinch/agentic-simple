"""Task definitions for the market research crew."""

from crewai import Task, Agent


def build_tasks(
    topic: str,
    researcher: Agent,
    analyst: Agent,
    visualizer: Agent,
    writer: Agent,
) -> list[Task]:
    """Build the task pipeline for a given research topic."""

    research_task = Task(
        description=(
            f"Research the following topic thoroughly: {topic}\n\n"
            "Identify:\n"
            "- Key players and their market positions\n"
            "- Market size estimates and growth trends\n"
            "- Competitive dynamics and differentiation\n"
            "- Technology trends and disruption vectors\n"
            "- Pricing and cost comparisons where available\n\n"
            "Structure your findings clearly with sections and bullet points."
        ),
        expected_output="A structured research report with key players, market data, trends, and competitive analysis.",
        agent=researcher,
    )

    analysis_task = Task(
        description=(
            "Transform the research findings into 2-4 quantitative chart datasets.\n\n"
            "For EACH chart, output a JSON block with exactly these fields:\n"
            "```json\n"
            "{\n"
            '  "chart_type": "bar",\n'
            '  "title": "Chart Title Here",\n'
            '  "labels": ["Label1", "Label2", "Label3"],\n'
            '  "values": [10, 20, 30],\n'
            '  "unit": "% or $ or description",\n'
            '  "filename": "descriptive_filename"\n'
            "}\n"
            "```\n\n"
            "Chart types available: bar, horizontal_bar, pie, line.\n"
            "Output ONLY the JSON blocks, one per chart. No other text."
        ),
        expected_output="2-4 JSON chart dataset blocks ready for visualization.",
        agent=analyst,
        context=[research_task],
    )

    visualization_task = Task(
        description=(
            "Generate charts from the analyst's JSON datasets using the ChartTool.\n\n"
            "For EACH JSON block from the analyst, call ChartTool with a single argument:\n"
            "chart_data - pass the entire JSON object as a string.\n\n"
            "Example call: ChartTool(chart_data='{\"chart_type\": \"bar\", \"title\": \"My Chart\", "
            "\"labels\": [\"A\", \"B\"], \"values\": [10, 20], \"unit\": \"%\", \"filename\": \"my_chart\"}')\n\n"
            "Generate ALL charts — do not skip any."
        ),
        expected_output="File paths to all generated chart PNG images.",
        agent=visualizer,
        context=[analysis_task],
    )

    writing_task = Task(
        description=(
            f"Write a polished markdown report on: {topic}\n\n"
            "Include these sections:\n"
            "1. Executive Summary (2-3 paragraphs)\n"
            "2. Key Players & Market Position\n"
            "3. Market Drivers and Trends\n"
            "4. Strategic Analysis\n"
            "5. Recommendations\n\n"
            "Embed chart references using: ![Chart Title](./charts/filename.png)\n"
            "Use the filenames from the visualization step.\n\n"
            "Save the final report using the FileTool with filename 'report'."
        ),
        expected_output="A complete markdown report saved to disk with embedded chart references.",
        agent=writer,
        context=[research_task, analysis_task, visualization_task],
    )

    return [research_task, analysis_task, visualization_task, writing_task]
