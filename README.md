# Akamai Edge AI Market Analyst

A live demo application showcasing hierarchical multi-agent AI running on Akamai Compute (Linode) GPU instances. A team of AI agents collaborates in real-time to research a topic, analyze data, generate visualizations, and produce a polished report — all visible through a WebSocket-driven dashboard.

---

## What This Demonstrates

This application is a working proof-of-concept for **agentic AI at the edge**. It shows:

1. **Multi-agent orchestration** — a larger "manager" model delegates to smaller specialist models, mirroring how real teams work
2. **GPU-efficient architecture** — a 27B parameter model orchestrates while 14B models execute, optimizing cost-per-task
3. **Real-time observability** — every agent action streams live to the browser via WebSocket
4. **Tool use** — agents generate charts and save reports using Python tools, demonstrating structured AI-to-code interaction
5. **Edge deployment model** — the application server runs on any VM; GPU inference stays on dedicated hardware accessed over private networking

---

## Architecture

```
                         Any VM (or local dev machine)
                    ┌─────────────────────────────────────┐
                    │  FastAPI Backend (:8000)             │
                    │  ┌──────────┐  ┌──────────────────┐ │
                    │  │ REST API │  │ WebSocket Stream  │ │
                    │  └────┬─────┘  └────────┬─────────┘ │
                    │       │    CrewAI        │           │
                    │       │  Orchestration   │           │
                    │       └────────┬─────────┘           │
                    │                │                     │
                    │  Svelte Frontend (built static)      │
                    └────────────────┼─────────────────────┘
                                     │ HTTP (Ollama API)
                          ┌──────────┴──────────┐
                          │                     │
               ┌──────────▼──────────┐ ┌───────▼────────────────┐
               │  VM1: RTX 6000 Pro  │ │  VM2: RTX 4000 Ada     │
               │  48GB VRAM          │ │  20GB VRAM              │
               │  Gemma 3 27B        │ │  Qwen 2.5 14B           │
               │  (Manager Agent)    │ │  (Specialist Agents)    │
               │  Ollama :11434      │ │  Ollama :11434          │
               └─────────────────────┘ └─────────────────────────┘
```

### Key Design Decision: Separated Compute

The application server does **not** need a GPU. It runs CrewAI, which makes HTTP calls to Ollama endpoints on the GPU VMs. This means:

- The demo can run from a laptop, a $5 Linode, or a CI runner — anywhere that can reach the GPU VMs
- GPU instances are dedicated to inference, not web serving
- You can scale by adding more GPU VMs without touching the application
- Development works locally in mock mode with zero GPU cost

### Hardware

| Role | GPU | Model | VRAM Usage | Purpose |
|------|-----|-------|------------|---------|
| Orchestrator | RTX 6000 Pro (48GB) | Gemma 3 27B (Q4_K_M) | ~17GB | Manager agent — plans, delegates, synthesizes |
| Specialists | RTX 4000 Ada (20GB) | Qwen 2.5 14B (Q4_K_M) | ~9GB | Research, analysis, visualization, writing |

---

## The Agent Team

CrewAI's **hierarchical process mode** means all communication flows through the manager. Specialist agents never talk to each other directly.

```
                    ┌─────────────────────┐
                    │  Manager (27B)      │
                    │  Plans & Delegates  │
                    └──┬───┬───┬───┬──────┘
                       │   │   │   │
              ┌────────┘   │   │   └────────┐
              ▼            ▼   ▼            ▼
         ┌──────────┐ ┌────────┐ ┌──────────┐ ┌────────┐
         │Researcher│ │Analyst │ │Visualizer│ │ Writer │
         │  (14B)   │ │ (14B)  │ │  (14B)   │ │ (14B)  │
         │          │ │        │ │ ChartTool│ │FileTool│
         └──────────┘ └────────┘ └──────────┘ └────────┘
```

| Agent | Role | Tools | Output |
|-------|------|-------|--------|
| **Manager** | Senior Research Director | None (delegates only) | Task decomposition and synthesis |
| **Researcher** | Market Research Specialist | None | Structured findings with sections and data |
| **Analyst** | Data Analyst | None | 2-4 JSON chart datasets |
| **Visualizer** | Data Visualization Specialist | ChartTool | PNG chart images (Akamai palette) |
| **Writer** | Report Writer | FileTool | Polished markdown report with embedded charts |

### Why Qwen 2.5 14B Over Gemma 3 12B

We initially deployed Gemma 3 12B for the specialist agents. During integration testing, we discovered several issues with Gemma's structured output:

- **Tool schema confusion** — Gemma would pass the tool's JSON schema definition as input instead of actual values
- **Parameter type errors** — passing Python lists where JSON strings were expected, and vice versa
- **Content leakage** — raw `ToolResult(...)` and `AgentFinish(...)` wrapper objects appearing in output
- **Instruction following** — the FileTool was called with the filename as content, and reports were wrapped in unnecessary `Thought:` preambles

Switching to **Qwen 2.5 14B** resolved these issues. Qwen 2.5 is specifically known for strong structured output and tool use capabilities. At 14B parameters (Q4 quantization, ~9GB VRAM), it fits comfortably on the RTX 4000 Ada's 20GB with room to spare.

This is a practical insight worth highlighting in demo discussions: **model selection for agentic workloads is about tool-use capability, not just raw intelligence.** A model that reliably follows tool schemas is more valuable than a larger model that doesn't.

---

## Real-Time Event Pipeline

The core technical challenge: CrewAI runs synchronously in a thread, but we need to stream agent activity to the browser in real-time.

```
CrewAI (sync thread)          FastAPI (async)              Browser
       │                            │                         │
       │ step_callback(output) ─────▶ push_event(dict) ──────▶ WebSocket
       │                            │                         │ JSON frame
       │ step_callback(output) ─────▶ push_event(dict) ──────▶ WebSocket
       │                            │                         │
       │ task_callback(result) ─────▶ push_event(delegation) ▶ WebSocket
       │                            │ push_event(agent_start) │
       │                            │                         │
       │ crew.kickoff() returns ────▶ push_event(complete) ──▶ WebSocket
       │                            │ mark_complete()         │ client closes
```

### CrewEventBridge

The bridge uses an **index-based consumer** pattern (not a queue):

- Events are appended to a list (`bridge.events`)
- WebSocket consumers iterate from any index using `consume_from(start_index)`
- An `asyncio.Event` notifies consumers when new events arrive
- Late-joining clients replay the full history automatically
- No events are ever lost (unlike queue-based approaches where a slow consumer drops messages)

### Agent Attribution in Hierarchical Mode

In CrewAI's hierarchical mode, the manager's executor runs all tasks. This means `step_callback` always fires from the manager's context — there's no built-in way to know which specialist agent is conceptually active.

Our solution: **index-based task tracking**. Tasks always execute in a fixed order (research → analysis → visualization → writing). A `task_callback` on the Crew fires when each task completes. We maintain a simple counter that advances through the known agent list, emitting `delegation` events between transitions.

### Defensive Output Handling

Small models produce unpredictable output. The pipeline includes multiple layers of cleanup:

1. **Content cleaning** (`_clean_content`) — strips `ToolResult(...)`, `AgentFinish(...)` wrappers, and `### Assistant:` prefixes via regex
2. **Report cleaning** (`_clean_report`) — strips `Thought:` preambles, markdown code fences
3. **Chart reference fixing** (`_fix_chart_refs`) — fuzzy-matches image paths in the report against actual chart files on disk, fixing wrong extensions (`.json` → `.png`) and wrong paths
4. **Multi-source report extraction** — checks three sources for the report (FileTool output, crew result, event stream) and picks the longest, because the writer may botch the FileTool call
5. **Chart filename sanitization** — strips file extensions from filenames before saving, so `chart.json` becomes `chart.png` not `chart_json.png`

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Model serving | [Ollama](https://ollama.com) | Simple setup, OpenAI-compatible API, native quantization |
| Agent framework | [CrewAI](https://github.com/crewai-io/crewai) | Hierarchical process mode, clean agent/task/tool abstractions |
| LLM routing | [LiteLLM](https://github.com/BerriAI/litellm) (via CrewAI) | `ollama/model:tag` strings route transparently to Ollama endpoints |
| Backend | [FastAPI](https://fastapi.tiangolo.com) + uvicorn | Async WebSocket support, REST endpoints, production-grade |
| Frontend | [SvelteKit](https://kit.svelte.dev) (Svelte 5) | Reactive UI, WebSocket-native, fast builds |
| Charts | [Matplotlib](https://matplotlib.org) + Seaborn | Akamai-palette chart generation as an agent tool |
| Deployment | GNU Make + shell scripts | `make setup` handles everything from drivers to model pull |

---

## Deployment

### Prerequisites

- Two Akamai/Linode GPU instances with Ollama running (see `setup/` scripts)
- Any machine that can reach both GPU VMs on port 11434

### Quick Start

```bash
git clone <repo-url>
cd akamai-edge-ai-analyst
cp .env.example .env
# Edit .env with your GPU VM IPs
```

Edit `.env`:
```bash
ORCHESTRATOR_HOST=<vm1-ip>       # RTX 6000 Pro running gemma3:27b
SPECIALIST_HOST=<vm2-ip>         # RTX 4000 Ada running qwen2.5:14b
MANAGER_MODEL=ollama/gemma3:27b
MANAGER_BASE_URL=http://<vm1-ip>:11434
SPECIALIST_MODEL=ollama/qwen2.5:14b
SPECIALIST_BASE_URL=http://<vm2-ip>:11434
MOCK_MODE=false
```

```bash
make venv               # Create Python 3.11 venv
make backend-install     # Install Python dependencies
make build               # Build Svelte frontend
make backend             # Start on port 8000
```

Or for development with hot reload:
```bash
make dev                 # Backend :8000 + Vite :5173 (proxied)
```

### Mock Mode (No GPUs)

```bash
# In .env:
MOCK_MODE=true

make dev
```

Mock mode simulates the full agent pipeline with realistic timed events, real chart generation, and a substantive report. Useful for:
- Frontend development without GPU cost
- Demo fallback if GPU connectivity fails
- CI/CD testing

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System readiness — Ollama reachability, model availability |
| `/api/warmup` | POST | Pre-load models into VRAM (reduces first-run latency) |
| `/api/crew/run` | POST | Start a crew run. Body: `{"topic": "..."}`. Returns `{"run_id": "..."}` |
| `/api/crew/status/{run_id}` | GET | Poll run state, event count, report path, charts |
| `/api/crew/report/{run_id}` | GET | Fetch completed report markdown + chart paths |
| `/api/crew/runs` | GET | List all runs |
| `/ws/crew/stream/{run_id}` | WebSocket | Real-time event stream for a run |

### WebSocket Event Types

| Type | Description | Key Fields |
|------|-------------|------------|
| `agent_start` | Agent begins work | `agent`, `role`, `model`, `vm`, `task_summary` |
| `agent_output` | Agent produces content | `agent`, `role`, `content` |
| `tool_use` | Agent calls a tool | `agent`, `tool`, `tool_input` |
| `delegation` | Manager hands off to next agent | `from`, `to`, `instruction` |
| `agent_complete` | Agent finishes its task | `agent`, `role` |
| `chart_created` | Chart image generated | `agent`, `chart_title`, `path` |
| `crew_complete` | All tasks done | `total_seconds`, `report_path`, `charts` |
| `error` | Something went wrong | `agent`, `message`, `recoverable` |

---

## Project Structure

```
akamai-edge-ai-analyst/
├── .env.example              # Template — copy to .env, set IPs
├── Makefile                  # Setup, build, deploy targets
│
├── backend/
│   ├── main.py               # FastAPI app — mounts routes + static files
│   ├── config.py             # Centralized env config + sqlite3 fix
│   ├── routers/
│   │   ├── crew_router.py    # /api/crew/* + /ws/crew/stream + report extraction
│   │   └── health_router.py  # /api/health + /api/warmup
│   ├── crew/
│   │   ├── agents.py         # 5 agent definitions (manager + specialists)
│   │   ├── tasks.py          # 4-task pipeline with context chaining
│   │   ├── crew.py           # Hierarchical crew assembly + task tracking
│   │   ├── callbacks.py      # CrewEventBridge — sync→async event bridge
│   │   ├── tools.py          # CrewAI @tool wrappers (ChartTool, FileTool)
│   │   ├── mock_runner.py    # Mock mode simulation (23 timed events)
│   │   └── run_manager.py    # Run state tracking (RunManager singleton)
│   └── tools/
│       ├── chart_tool.py     # Matplotlib chart generation (Akamai palette)
│       └── file_tool.py      # File saving utility
│
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── websocket.ts       # WebSocket client with reconnect
│   │   │   ├── types.ts           # TypeScript types + agent color map
│   │   │   ├── stores/crew.ts     # Svelte stores for crew state
│   │   │   └── components/
│   │   │       ├── TopicInput.svelte    # Topic input + presets + Go
│   │   │       ├── AgentLog.svelte      # Live scrolling event feed
│   │   │       ├── ReportView.svelte    # Markdown rendering + chart images
│   │   │       ├── InfraPanel.svelte    # GPU/model status panel
│   │   │       └── ...
│   │   └── routes/+page.svelte    # Main page layout
│   └── static/favicon.png
│
├── setup/                    # VM provisioning scripts
│   ├── common.sh             # OS packages, NVIDIA drivers, Docker, Node.js
│   ├── ollama.sh             # Ollama install + model pull
│   ├── firewall.sh           # UFW rules per role
│   └── vlan.sh               # Optional VLAN IP config
│
├── docs/
│   ├── vlan-setup.md         # VLAN setup guide (optional)
│   └── demo-script.md        # Presenter run-of-show
│
└── demo/
    └── sample-topics.txt     # Pre-tested research topics
```

---

## Lessons Learned

### Model Selection Matters More Than Model Size

Gemma 3 12B and Qwen 2.5 14B are similar in parameter count, but their agentic capabilities differ dramatically. Qwen 2.5 handles tool schemas, JSON output, and multi-step instructions far more reliably. For agentic workloads, and especially for smaller parameter models, **evaluate models on tool-use benchmarks, not just general benchmarks**.

### Defensive Output Handling Is Non-Negotiable

Even good models produce inconsistent output under agentic orchestration. Every tool input, every report output, every file path needs validation and cleanup. Assume the model will:
- Wrap output in unexpected containers (`ToolResult(...)`, code fences)
- Use wrong file extensions or paths
- Pass schemas where values are expected
- Include chain-of-thought reasoning in final output

### Hierarchical Mode Changes the Callback Model

CrewAI's hierarchical process routes all execution through the manager agent's executor. Per-agent callbacks on specialist agents don't fire — you need to track agent transitions at the task level and attribute events based on task order.

### Event Streaming Needs Index-Based Consumers, Not Queues

Queue-based event consumers lose messages when consumers are slow or connect late. An append-only event list with index-based iteration and `asyncio.Event` notification is simpler, more reliable, and supports replay for late-joining clients.

### Mock Mode Is Essential

Having a complete mock mode that generates real charts and streams realistic events enabled weeks of frontend development without GPU costs, and serves as an instant demo fallback.

---

## Running a Demo

See [docs/demo-script.md](docs/demo-script.md) for the full presenter run-of-show, including pre-demo checklist, narration guide, talking points, and Q&A prep.

```bash
make test      # Verify GPU, Ollama, API, frontend
make warmup    # Pre-load models into VRAM
# Open http://<host>:8000 in browser
# Select topic → Go → Watch agents work → Report appears
```
