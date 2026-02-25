include .env
export

VENV := .venv
SYSTEM_PYTHON := $(shell command -v python3.11 || command -v python3.12 || command -v python3)
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

.PHONY: help setup setup-base setup-ollama setup-vlan setup-firewall \
        backend backend-dev backend-install venv \
        frontend frontend-dev frontend-install \
        deploy dev build run warmup test status logs clean restart mock

# ── Help ──
help:
	@echo "Akamai Edge AI Market Analyst"
	@echo ""
	@echo "Setup (run on both VMs):"
	@echo "  make setup             Full VM setup (reads ROLE from .env)"
	@echo "  make setup-base        OS packages, NVIDIA driver check, Docker, Node.js"
	@echo "  make setup-ollama      Install Ollama, configure systemd, pull model"
	@echo "  make setup-vlan        Configure VLAN IP via Netplan"
	@echo "  make setup-firewall    UFW rules per ROLE"
	@echo ""
	@echo "Backend (VM1):"
	@echo "  make backend           Run uvicorn in production mode (port 8000)"
	@echo "  make backend-dev       Run uvicorn with --reload for development"
	@echo "  make backend-install   pip install -r backend/requirements.txt"
	@echo ""
	@echo "Frontend (VM1):"
	@echo "  make frontend          Build Svelte for production"
	@echo "  make frontend-dev      Run Vite dev server (port 5173)"
	@echo "  make frontend-install  npm install in frontend/"
	@echo ""
	@echo "Combined:"
	@echo "  make deploy            docker compose up -d (production)"
	@echo "  make dev               Run backend-dev and frontend-dev concurrently"
	@echo "  make build             frontend-install + frontend (full production build)"
	@echo ""
	@echo "Operations:"
	@echo "  make run               Run crew via CLI (no UI, for testing)"
	@echo "  make warmup            Pre-load models into VRAM"
	@echo "  make test              Verify VLAN, Ollama, API health"
	@echo "  make status            GPU, Ollama, VLAN, Docker status"
	@echo "  make logs              Tail backend + crew logs"
	@echo "  make clean             Stop containers, clear output/"
	@echo "  make restart           docker compose down && up"
	@echo ""
	@echo "Development:"
	@echo "  make mock              Run in mock mode (no GPUs needed)"

# ── VM Setup ──
setup: setup-base setup-ollama setup-firewall
	@echo "✓ Setup complete for role: $(ROLE)"

setup-base:
	sudo bash setup/common.sh

setup-ollama:
ifeq ($(ROLE),orchestrator)
	sudo bash setup/ollama.sh gemma3:27b
else
	sudo bash setup/ollama.sh gemma3:12b
endif

setup-vlan:
ifeq ($(ROLE),orchestrator)
	sudo bash setup/vlan.sh $(ORCHESTRATOR_HOST)
else
	sudo bash setup/vlan.sh $(SPECIALIST_HOST)
endif

setup-firewall:
	sudo bash setup/firewall.sh $(ROLE)

# ── Python venv ──
venv:
	@test -d $(VENV) || $(SYSTEM_PYTHON) -m venv $(VENV)
	@echo "✓ venv ready"

# ── Backend ──
backend: backend-install
	$(UVICORN) backend.main:app --host 0.0.0.0 --port 8000

backend-dev: backend-install
	$(UVICORN) backend.main:app --host 0.0.0.0 --port 8000 --reload

backend-install: venv
	$(PIP) install -q -r backend/requirements.txt

# ── Frontend ──
frontend: frontend-install
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev -- --host 0.0.0.0

frontend-install:
	cd frontend && npm install

# ── Combined ──
build: frontend-install frontend

deploy:
	docker compose up -d

dev:
	@echo "Starting backend and frontend in dev mode..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	$(MAKE) backend-dev & $(MAKE) frontend-dev & wait

# ── Operations ──
run:
	$(PYTHON) -m backend.crew.cli

warmup:
	@echo "Warming up models..."
	curl -sf -X POST http://localhost:8000/api/warmup | jq .

test:
	@echo "Running checks..."
	@bash -c '\
		OK=0; FAIL=0; \
		check() { if eval "$$2" >/dev/null 2>&1; then echo "  ✓ $$1"; ((OK++)); else echo "  ✗ $$1"; ((FAIL++)); fi; }; \
		echo "System:"; \
		check "NVIDIA GPU" "nvidia-smi"; \
		check "Docker" "docker info"; \
		echo "Ollama:"; \
		check "Ollama local" "curl -sf http://localhost:11434/api/tags"; \
		check "Ollama specialist" "curl -sf http://$(SPECIALIST_HOST):11434/api/tags"; \
		echo "App:"; \
		check "API health" "curl -sf http://localhost:8000/api/health"; \
		check "Frontend" "curl -sf http://localhost:8000/ | grep -q html"; \
		echo ""; \
		echo "$$OK passed, $$FAIL failed" \
	'

status:
	@echo "── GPU ──"
	@nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo "No GPU detected"
	@echo ""
	@echo "── Ollama ──"
	@curl -sf http://localhost:11434/api/tags | jq -r '.models[]?.name' 2>/dev/null || echo "Ollama not running"
	@echo ""
	@echo "── Docker ──"
	@docker compose ps 2>/dev/null || echo "No containers running"

logs:
	docker compose logs -f --tail=100

clean:
	docker compose down 2>/dev/null || true
	rm -rf backend/output/charts/*.png backend/output/*.md backend/output/*.txt
	@echo "✓ Cleaned"

restart:
	docker compose down && docker compose up -d

# ── Development ──
mock:
	MOCK_MODE=true $(MAKE) dev
