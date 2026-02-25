"""Matplotlib chart generation tool for the Visualizer agent."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from backend.config import CHARTS_DIR

# Akamai palette
COLORS = ["#009BDE", "#00D4AA", "#6366F1", "#EAB308", "#EF4444", "#94A3B8"]


def generate_chart(
    chart_type: str,
    title: str,
    labels: list[str],
    values: list[float],
    unit: str = "",
    filename: str = "chart",
    values_2: list[float] | None = None,
    series_labels: list[str] | None = None,
) -> str:
    """Generate a chart and return the file path relative to output/."""
    # Clean filename — strip any extension the LLM may have added
    filename = Path(filename).stem
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#0D1B2A")
    ax.set_facecolor("#0D1B2A")

    colors = COLORS[: len(labels)]

    try:
        if chart_type == "pie":
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
                textprops={"color": "#E2E8F0", "fontsize": 11},
            )
            for t in autotexts:
                t.set_fontsize(10)
                t.set_color("#E2E8F0")

        elif chart_type == "horizontal_bar":
            y_pos = range(len(labels))
            bars = ax.barh(y_pos, values, color=colors, height=0.6)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=11)
            ax.invert_yaxis()
            if unit:
                ax.set_xlabel(unit, fontsize=11, color="#94A3B8")
            # Value labels on bars
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_width() + max(values) * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val}{' ' + unit if unit and '%' not in unit else ''}",
                    va="center",
                    fontsize=10,
                    color="#E2E8F0",
                )

        elif chart_type == "line":
            ax.plot(labels, values, color=COLORS[0], linewidth=2.5, marker="o", markersize=8)
            if values_2 and series_labels:
                ax.plot(labels, values_2, color=COLORS[1], linewidth=2.5, marker="s", markersize=8)
                ax.legend(series_labels, fontsize=10, facecolor="#1E293B", edgecolor="#334155")
            ax.fill_between(labels, values, alpha=0.1, color=COLORS[0])
            if unit:
                ax.set_ylabel(unit, fontsize=11, color="#94A3B8")

        else:  # bar (default)
            x_pos = range(len(labels))
            bars = ax.bar(x_pos, values, color=colors, width=0.6)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, fontsize=10, rotation=30, ha="right")
            if unit:
                ax.set_ylabel(unit, fontsize=11, color="#94A3B8")
            # Value labels above bars
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(values) * 0.02,
                    f"{val}",
                    ha="center",
                    fontsize=10,
                    color="#E2E8F0",
                )

    except Exception:
        # Fallback: simple bar chart
        ax.bar(range(len(labels)), values, color=COLORS[0])
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=10, rotation=30, ha="right")

    ax.set_title(title, fontsize=14, color="#E2E8F0", pad=15, fontweight="bold")
    ax.tick_params(colors="#94A3B8")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    ax.grid(axis="y", alpha=0.15, color="#94A3B8")

    # Save
    safe_filename = "".join(c if c.isalnum() or c in "-_" else "_" for c in filename)
    filepath = CHARTS_DIR / f"{safe_filename}.png"
    fig.tight_layout()
    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#0D1B2A")
    plt.close(fig)

    return f"charts/{safe_filename}.png"
