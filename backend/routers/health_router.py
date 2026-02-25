"""Health and warmup endpoints."""

from fastapi import APIRouter
import httpx

from backend.config import (
    MANAGER_BASE_URL, SPECIALIST_BASE_URL,
    MANAGER_MODEL, SPECIALIST_MODEL, MOCK_MODE,
)

router = APIRouter()


async def _check_ollama(base_url: str) -> dict:
    """Check if an Ollama instance is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                return {"reachable": True, "models": models}
    except Exception:
        pass
    return {"reachable": False, "models": []}


@router.get("/health")
async def health():
    if MOCK_MODE:
        return {
            "status": "ok",
            "mock_mode": True,
            "orchestrator": {"ollama": True, "model": MANAGER_MODEL},
            "specialist": {"ollama": True, "model": SPECIALIST_MODEL},
        }

    orch = await _check_ollama(MANAGER_BASE_URL)
    spec = await _check_ollama(SPECIALIST_BASE_URL)

    status = "ok" if orch["reachable"] and spec["reachable"] else "degraded"
    if not orch["reachable"] and not spec["reachable"]:
        status = "unavailable"

    return {
        "status": status,
        "mock_mode": False,
        "orchestrator": {"ollama": orch["reachable"], "models": orch["models"]},
        "specialist": {"ollama": spec["reachable"], "models": spec["models"]},
    }


@router.post("/warmup")
async def warmup():
    """Send a short prompt to both Ollama endpoints to pre-load models into VRAM."""
    if MOCK_MODE:
        return {"orchestrator_ms": 0, "specialist_ms": 0, "mock_mode": True}

    import time

    async def _warmup(base_url: str, model: str) -> int:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                await client.post(
                    f"{base_url}/api/generate",
                    json={"model": model.split("/")[-1], "prompt": "Hello", "stream": False},
                )
        except Exception:
            return -1
        return int((time.monotonic() - start) * 1000)

    orch_ms = await _warmup(MANAGER_BASE_URL, MANAGER_MODEL)
    spec_ms = await _warmup(SPECIALIST_BASE_URL, SPECIALIST_MODEL)

    return {"orchestrator_ms": orch_ms, "specialist_ms": spec_ms}
