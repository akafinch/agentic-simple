"""Agent definitions for the market research crew."""

from crewai import Agent, LLM

from backend.config import (
    MANAGER_MODEL, MANAGER_BASE_URL,
    SPECIALIST_MODEL, SPECIALIST_BASE_URL,
)


def _manager_llm() -> LLM:
    return LLM(
        model=MANAGER_MODEL,
        base_url=MANAGER_BASE_URL,
    )


def _specialist_llm() -> LLM:
    return LLM(
        model=SPECIALIST_MODEL,
        base_url=SPECIALIST_BASE_URL,
    )


def build_manager() -> Agent:
    return Agent(
        role="Senior Research Director",
        goal="Produce a comprehensive, well-structured market analysis with data visualizations",
        backstory=(
            "You are a senior research director at a leading technology advisory firm. "
            "You excel at decomposing complex research questions into actionable tasks, "
            "delegating effectively, and synthesizing diverse inputs into coherent, "
            "insight-driven reports."
        ),
        llm=_manager_llm(),
        allow_delegation=True,
        verbose=True,
    )


def build_researcher() -> Agent:
    return Agent(
        role="Market Research Specialist",
        goal="Gather comprehensive information — key players, trends, competitive dynamics",
        backstory=(
            "You are a meticulous market research specialist who excels at gathering, "
            "organizing, and synthesizing information from multiple angles. You always "
            "structure findings clearly with sections and bullet points."
        ),
        llm=_specialist_llm(),
        allow_delegation=False,
        verbose=True,
    )


def build_analyst() -> Agent:
    return Agent(
        role="Data Analyst",
        goal="Transform research into quantitative insights and structured chart-ready datasets",
        backstory=(
            "You transform qualitative research into quantitative insights. You estimate "
            "market sizes, create comparative frameworks, and output clean structured data. "
            "You ALWAYS output chart data as JSON blocks with these exact fields: "
            "chart_type (bar/horizontal_bar/pie/line), title, labels (list of strings), "
            "values (list of numbers), unit, filename."
        ),
        llm=_specialist_llm(),
        allow_delegation=False,
        verbose=True,
    )


def build_visualizer(tools: list) -> Agent:
    return Agent(
        role="Data Visualization Specialist",
        goal="Create 2-4 clear, professional charts from the analyst's data",
        backstory=(
            "You create compelling, presentation-ready charts. You receive JSON chart "
            "datasets and use the ChartTool to generate each chart. For each chart, "
            "call the tool with the exact JSON data provided by the analyst. "
            "Always generate all charts requested."
        ),
        llm=_specialist_llm(),
        tools=tools,
        allow_delegation=False,
        verbose=True,
    )


def build_writer(tools: list) -> Agent:
    return Agent(
        role="Report Writer",
        goal="Produce a polished markdown report with executive summary, analysis, chart references, and recommendations",
        backstory=(
            "You create executive-ready reports. You incorporate data visualizations "
            "by reference using markdown image syntax: ![Chart Title](./charts/filename.png). "
            "Write in a confident, analytical tone with clear sections: "
            "Executive Summary, Key Players, Market Drivers, Strategic Position, Recommendations."
        ),
        llm=_specialist_llm(),
        tools=tools,
        allow_delegation=False,
        verbose=True,
    )
