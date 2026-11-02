from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.agent.containerd.client import ContainerRecord, TaskInfo


class FakeContainerd:
    """An in-memory containerd: containers and tasks."""

    containers: dict[str, ContainerRecord]
    tasks: dict[str, TaskInfo]
    calls: list[str]
    closed: bool
    connected: bool

    def __init__(self) -> None:
        self.containers = {}
        self.tasks = {}
        self.calls = []
        self.closed = False
        self.connected = True

    async def connect(self) -> None:
        self.connected = True

    async def close(self) -> None:
        self.closed = True

    async def list_containers(self, labels: Mapping[str, str]) -> Sequence[ContainerRecord]:
        self.calls.append("list_containers")
        return [
            c
            for c in self.containers.values()
            if all(k in c.labels and (not v or c.labels[k] == v) for k, v in labels.items())
        ]

    async def get_task(self, container_id: str) -> TaskInfo | None:
        self.calls.append("get_task")
        return self.tasks.get(container_id)
