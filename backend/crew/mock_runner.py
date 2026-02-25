"""Mock crew runner — simulates a full crew run with realistic timing and content."""

import asyncio
from datetime import datetime, timezone

from backend.crew.run_manager import CrewRun
from backend.tools.chart_tool import generate_chart
from backend.tools.file_tool import save_report


# ── Mock chart datasets ──

MOCK_CHARTS = [
    {
        "chart_type": "horizontal_bar",
        "title": "Edge AI Inference Market Share by Provider (2025 Est.)",
        "labels": ["AWS Inferentia", "Azure AI", "Google Cloud TPU", "CoreWeave", "Lambda Labs", "Akamai / Linode"],
        "values": [31, 24, 18, 12, 8, 4],
        "unit": "% market share",
        "filename": "market_share",
    },
    {
        "chart_type": "line",
        "title": "Edge AI Inference Market Growth (2022-2027)",
        "labels": ["2022", "2023", "2024", "2025", "2026", "2027"],
        "values": [8.2, 14.6, 24.1, 38.5, 58.3, 82.0],
        "unit": "$ Billions",
        "filename": "market_growth",
    },
    {
        "chart_type": "bar",
        "title": "GPU Cloud Cost Comparison (per GPU-hour)",
        "labels": ["AWS p5", "Azure ND", "GCP A3", "CoreWeave", "Lambda", "Akamai"],
        "values": [32.77, 29.40, 31.22, 18.50, 14.80, 12.50],
        "unit": "$/hr",
        "filename": "cost_comparison",
    },
]


# ── Mock report ──

MOCK_REPORT = """# Edge AI Inference: Competitive Landscape Analysis

## Executive Summary

The edge AI inference market is experiencing explosive growth, projected to reach **$82B by 2027** at a CAGR of 58.9%. While hyperscalers dominate current market share, a significant opportunity exists for **cost-competitive, GPU-native cloud providers** to capture workloads that demand low latency, data sovereignty, and predictable pricing.

This analysis examines the competitive dynamics, identifies key market drivers, and evaluates Akamai's strategic position as it enters the edge AI inference space through its Linode GPU infrastructure.

---

## Key Players & Market Position

### Hyperscaler Dominance (73% combined share)
- **AWS Inferentia/Trainium** (31%): Custom silicon strategy with Inf2 instances. Strong ecosystem lock-in through SageMaker. Premium pricing reflects brand tax.
- **Azure AI** (24%): Tight coupling with OpenAI partnership. NC-series GPU instances. Enterprise agreements drive adoption.
- **Google Cloud TPU** (18%): TPU v5e offers best price/performance for transformer workloads. But limited to Google's ecosystem.

### GPU-Native Challengers (24% combined, growing fast)
- **CoreWeave** (12%): Purpose-built GPU cloud. NVIDIA partnership. 60-80% cheaper than hyperscalers for sustained workloads.
- **Lambda Labs** (8%): Developer-focused. Reserved GPU clusters. Strong ML community presence.
- **Akamai / Linode** (4%): Newest entrant. RTX 4000/6000 Ada instances in select regions. Edge network advantage is unique differentiator.

---

## Market Drivers

1. **Latency sensitivity**: Real-time inference (video analytics, content moderation, autonomous systems) cannot tolerate round-trips to centralized clouds.
2. **Data sovereignty**: GDPR, healthcare regulations, and financial compliance require processing at the point of data generation.
3. **Cost pressure**: Hyperscaler GPU pricing is 2-4x higher than GPU-native alternatives for sustained workloads.
4. **Model efficiency gains**: Quantization (GPTQ, AWQ), distillation, and smaller models (Gemma, Phi, Llama) make edge deployment viable on mid-tier GPUs.

---

## Akamai's Strategic Position

### Strengths
- **Global edge network**: 4,200+ PoPs provide unmatched geographic reach for low-latency inference
- **Cost structure**: Linode GPU instances priced 40-60% below hyperscaler equivalents
- **Developer trust**: Linode community brings cloud-native developers who value simplicity
- **Network integration**: Unique ability to combine CDN intelligence with compute placement

### Challenges
- **GPU fleet scale**: Currently limited regions and GPU SKUs vs. hyperscaler breadth
- **ML ecosystem**: No equivalent to SageMaker, Vertex AI, or Azure ML for managed ML ops
- **Enterprise sales motion**: Building enterprise AI buyer relationships takes time

---

## Recommendations

1. **Lead with price/performance**: The cost comparison data shows Akamai at $12.50/GPU-hr vs. $32.77 for AWS — make this the headline.
2. **Target latency-sensitive workloads**: Content moderation, real-time video analytics, and gaming AI where edge placement matters.
3. **Build inference-specific tooling**: One-click model deployment, auto-scaling, and monitoring dashboards purpose-built for inference.
4. **Partner for ecosystem**: Integrate with Ollama, vLLM, and TensorRT to meet developers where they are.

---

## Data Visualizations

![Edge AI Inference Market Share by Provider (2025 Est.)](./charts/market_share.png)

![Edge AI Inference Market Growth (2022-2027)](./charts/market_growth.png)

![GPU Cloud Cost Comparison (per GPU-hour)](./charts/cost_comparison.png)

---

*Report generated by Akamai Edge AI Market Analyst — a multi-agent system running on Akamai GPU infrastructure.*
"""


# ── Mock event sequence ──

def _build_event_sequence(topic: str, chart_paths: list[str]) -> list[tuple[float, dict]]:
    """Returns list of (delay_seconds, event_dict) pairs."""
    return [
        # Manager plans
        (0.5, {
            "type": "agent_start",
            "agent": "manager",
            "role": "Senior Research Director",
            "model": "gemma3:27b",
            "vm": "orchestrator",
            "task_summary": f"Planning research approach for: {topic}",
        }),
        (2.0, {
            "type": "agent_output",
            "agent": "manager",
            "content": f"I'll coordinate a comprehensive analysis of this topic. Let me delegate to our specialist team.\n\nResearch plan:\n1. Market research — gather key players, trends, and competitive dynamics\n2. Data analysis — produce quantitative datasets for visualization\n3. Chart generation — create presentation-ready visualizations\n4. Report writing — synthesize everything into an executive report",
        }),

        # Delegate to Researcher
        (1.5, {
            "type": "delegation",
            "from": "manager",
            "to": "researcher",
            "instruction": "Conduct comprehensive market research on edge AI inference providers. Identify key players, market shares, growth trends, and competitive dynamics.",
        }),
        (0.5, {
            "type": "agent_start",
            "agent": "researcher",
            "role": "Market Research Specialist",
            "model": "gemma3:12b",
            "vm": "specialist",
            "task_summary": "Researching edge AI inference competitive landscape",
        }),
        (3.0, {
            "type": "agent_output",
            "agent": "researcher",
            "content": "## Initial Research Findings\n\nThe edge AI inference market is segmented into three tiers:\n\n**Tier 1 — Hyperscalers** (73% market share)\n- AWS Inferentia/Trainium: Custom silicon, SageMaker ecosystem\n- Azure AI: OpenAI partnership, NC-series GPUs\n- Google Cloud TPU: Best transformer price/performance\n\n**Tier 2 — GPU-Native Challengers** (24%)\n- CoreWeave: Purpose-built GPU cloud, 60-80% cheaper\n- Lambda Labs: Developer-focused reserved clusters\n\n**Tier 3 — Edge-Native Entrants** (3-4%)\n- Akamai/Linode: RTX Ada instances, edge network advantage",
        }),
        (2.5, {
            "type": "agent_output",
            "agent": "researcher",
            "content": "## Market Dynamics\n\n- Market size: ~$38.5B in 2025, projected $82B by 2027 (58.9% CAGR)\n- Key drivers: latency requirements, data sovereignty regulations, cost pressure\n- Disruption vector: smaller quantized models (Gemma, Phi, Llama) enable mid-tier GPU deployment\n- Pricing gap: hyperscalers charge 2-4x premium over GPU-native alternatives",
        }),
        (1.0, {
            "type": "agent_complete",
            "agent": "researcher",
            "elapsed_seconds": 9,
        }),

        # Delegate to Analyst
        (1.0, {
            "type": "delegation",
            "from": "manager",
            "to": "analyst",
            "instruction": "Transform the research findings into quantitative datasets suitable for chart generation. Produce 2-3 JSON chart datasets covering market share, growth trends, and cost comparison.",
        }),
        (0.5, {
            "type": "agent_start",
            "agent": "analyst",
            "role": "Data Analyst",
            "model": "gemma3:12b",
            "vm": "specialist",
            "task_summary": "Producing chart-ready datasets from research",
        }),
        (3.0, {
            "type": "agent_output",
            "agent": "analyst",
            "content": '## Chart Datasets Prepared\n\n**Dataset 1: Market Share (horizontal bar)**\nProviders ranked by estimated 2025 market share percentage.\n\n**Dataset 2: Market Growth (line)**\nYear-over-year market size from $8.2B (2022) to projected $82B (2027).\n\n**Dataset 3: Cost Comparison (bar)**\nPer-GPU-hour pricing across providers — highlights Akamai\'s cost advantage.',
        }),
        (1.0, {
            "type": "agent_complete",
            "agent": "analyst",
            "elapsed_seconds": 6,
        }),

        # Delegate to Visualizer
        (1.0, {
            "type": "delegation",
            "from": "manager",
            "to": "visualizer",
            "instruction": "Generate professional charts from the analyst's datasets using the ChartTool. Create all three visualizations with the Akamai color palette.",
        }),
        (0.5, {
            "type": "agent_start",
            "agent": "visualizer",
            "role": "Data Visualization Specialist",
            "model": "gemma3:12b",
            "vm": "specialist",
            "task_summary": "Generating presentation-ready charts",
        }),
        (2.0, {
            "type": "chart_created",
            "agent": "visualizer",
            "chart_title": "Edge AI Inference Market Share by Provider (2025 Est.)",
            "path": f"/output/{chart_paths[0]}" if chart_paths else "/output/charts/market_share.png",
        }),
        (2.0, {
            "type": "chart_created",
            "agent": "visualizer",
            "chart_title": "Edge AI Inference Market Growth (2022-2027)",
            "path": f"/output/{chart_paths[1]}" if len(chart_paths) > 1 else "/output/charts/market_growth.png",
        }),
        (2.0, {
            "type": "chart_created",
            "agent": "visualizer",
            "chart_title": "GPU Cloud Cost Comparison (per GPU-hour)",
            "path": f"/output/{chart_paths[2]}" if len(chart_paths) > 2 else "/output/charts/cost_comparison.png",
        }),
        (1.0, {
            "type": "agent_complete",
            "agent": "visualizer",
            "elapsed_seconds": 8,
        }),

        # Delegate to Writer
        (1.0, {
            "type": "delegation",
            "from": "manager",
            "to": "writer",
            "instruction": "Produce a polished markdown report incorporating the research, analysis, and chart references. Include an executive summary, key findings, and strategic recommendations.",
        }),
        (0.5, {
            "type": "agent_start",
            "agent": "writer",
            "role": "Report Writer",
            "model": "gemma3:12b",
            "vm": "specialist",
            "task_summary": "Writing final markdown report",
        }),
        (4.0, {
            "type": "agent_output",
            "agent": "writer",
            "content": "Report drafted with executive summary, competitive analysis, market drivers, strategic positioning, and embedded chart references. Saving to file...",
        }),
        (1.5, {
            "type": "agent_complete",
            "agent": "writer",
            "elapsed_seconds": 7,
        }),

        # Manager wraps up
        (1.0, {
            "type": "agent_output",
            "agent": "manager",
            "content": "All specialist agents have completed their tasks. The final report includes comprehensive market research, three data visualizations, and strategic recommendations. Review complete — delivering results.",
        }),
    ]


async def run_mock_crew(run: CrewRun):
    """Simulate a full crew run with timed events, real charts, and a real report."""
    import logging
    logger = logging.getLogger("mock_runner")

    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    bridge = run.bridge

    try:
        # Generate real charts
        chart_paths = []
        for chart_data in MOCK_CHARTS:
            path = generate_chart(**chart_data)
            chart_paths.append(path)
        run.charts = [f"/output/{p}" for p in chart_paths]

        # Save real report
        report_filename = save_report("report", MOCK_REPORT)
        run.report_path = f"/output/{report_filename}"

        # Stream events with timing
        events = _build_event_sequence(run.topic, chart_paths)
        total_elapsed = 0.0

        for i, (delay, event) in enumerate(events):
            await asyncio.sleep(delay)
            total_elapsed += delay
            logger.info(f"[{run.run_id}] Pushing event {i+1}/{len(events)}: {event['type']} agent={event.get('agent', event.get('from', ''))}")
            bridge.push_event(event)

        logger.info(f"[{run.run_id}] All sequence events pushed. Pushing crew_complete...")

        # Final crew_complete event
        run.completed_at = datetime.now(timezone.utc)
        bridge.push_event({
            "type": "crew_complete",
            "total_seconds": round(total_elapsed, 1),
            "report_path": run.report_path,
            "charts": run.charts,
        })

        logger.info(f"[{run.run_id}] crew_complete pushed. Queue size: {bridge.queue.qsize()}")
        run.status = "completed"

    except Exception as e:
        logger.error(f"[{run.run_id}] Mock runner error: {e}")
        run.status = "error"
        run.error = str(e)
        bridge.push_event({
            "type": "error",
            "agent": "system",
            "message": str(e),
            "recoverable": False,
        })

    finally:
        logger.info(f"[{run.run_id}] Calling mark_complete()")
        bridge.mark_complete()
