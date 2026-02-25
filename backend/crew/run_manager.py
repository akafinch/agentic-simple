"""Tracks active and completed crew runs."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.crew.callbacks import CrewEventBridge


@dataclass
class CrewRun:
    run_id: str
    topic: str
    status: str = "pending"  # pending | running | completed | error
    bridge: CrewEventBridge = field(default=None)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report_path: Optional[str] = None
    charts: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        if self.bridge is None:
            self.bridge = CrewEventBridge(self.run_id)

    @property
    def elapsed_seconds(self) -> Optional[float]:
        if not self.started_at:
            return None
        end = self.completed_at or datetime.now(timezone.utc)
        return round((end - self.started_at).total_seconds(), 1)


class RunManager:
    """Singleton-ish manager for crew runs."""

    def __init__(self):
        self._runs: dict[str, CrewRun] = {}

    def create_run(self, run_id: str, topic: str) -> CrewRun:
        run = CrewRun(run_id=run_id, topic=topic)
        self._runs[run_id] = run
        return run

    def get_run(self, run_id: str) -> Optional[CrewRun]:
        return self._runs.get(run_id)

    def list_runs(self) -> list[dict]:
        return [
            {
                "run_id": r.run_id,
                "topic": r.topic,
                "status": r.status,
                "elapsed_seconds": r.elapsed_seconds,
            }
            for r in self._runs.values()
        ]


# Module-level singleton
run_manager = RunManager()
