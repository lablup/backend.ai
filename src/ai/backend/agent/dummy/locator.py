"""The ContainerLocator for the Dummy backend, which runs no containers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import override

from ai.backend.agent.network.locator import ContainerLocator, LiveContainer

__all__ = ("DummyContainerLocator",)


class DummyContainerLocator(ContainerLocator):
    """Reports no running containers: the Dummy agent creates none."""

    @override
    async def open(self) -> None:
        pass

    @override
    async def container_pid(self, container_id: str) -> int | None:
        return None

    @override
    async def live_sessions(self) -> Mapping[str, LiveContainer]:
        return {}
