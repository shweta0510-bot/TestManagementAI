"""Repository of pipelines on the Zara platform.

The pending feature asks this repository whether any pipeline is still
waiting for setup. Creation runs only when that list is empty.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from uuid import uuid4


class PipelineStatus(str, Enum):
    PENDING_SETUP = "Pending Setup"
    READY = "Ready"


class Pipeline:
    def __init__(self, pipeline_id: str, name: str, status: PipelineStatus) -> None:
        self.id = pipeline_id
        self.name = name
        self.status = status

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name, "status": self.status.value}

    @classmethod
    def from_dict(cls, payload: dict[str, str]) -> Pipeline:
        return cls(
            pipeline_id=payload["id"],
            name=payload["name"],
            status=PipelineStatus(payload["status"]),
        )


class ZaraPipelineRepository:
    """In-memory repository of Zara pipelines."""

    def __init__(self, pipelines: list[Pipeline] | None = None) -> None:
        self._pipelines = list(pipelines or [])

    def all(self) -> list[Pipeline]:
        return list(self._pipelines)

    def find_pending_setup(self) -> list[Pipeline]:
        return [
            pipeline
            for pipeline in self._pipelines
            if pipeline.status is PipelineStatus.PENDING_SETUP
        ]

    def has_pending_setup(self) -> bool:
        return bool(self.find_pending_setup())

    def add(self, pipeline: Pipeline) -> Pipeline:
        self._pipelines.append(pipeline)
        return pipeline

    def create_pending(self, name: str = "Generated pipeline") -> Pipeline:
        pipeline = Pipeline(
            pipeline_id=f"pipeline-{uuid4().hex[:8]}",
            name=name,
            status=PipelineStatus.PENDING_SETUP,
        )
        return self.add(pipeline)


class JsonZaraPipelineRepository(ZaraPipelineRepository):
    """Zara pipeline repository stored as JSON so runs share the same pool."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(self._read(path))

    @staticmethod
    def _read(path: Path) -> list[Pipeline]:
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [Pipeline.from_dict(item) for item in payload.get("pipelines", [])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = {"pipelines": [pipeline.to_dict() for pipeline in self._pipelines]}
        self.path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

    def add(self, pipeline: Pipeline) -> Pipeline:
        added = super().add(pipeline)
        self.save()
        return added
