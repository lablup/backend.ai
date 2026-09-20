"""The ContainerLocator every OCI-spec backend gets for free.

containerd, podman, enroot and singularity all drive an ``OciRuntime`` and all place their
containers under BAI's own cgroup layout, so one adapter answers the privnet for all four. Docker
does neither and brings its own (see ai.backend.agent.docker.locator).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import override

from ai.backend.agent.containerd.oci import OWNER_AGENT_LABEL, SESSION_ID_LABEL
from ai.backend.agent.containerd.runtime.spec import container_cgroup_fs_path
from ai.backend.agent.network.locator import ContainerLocator, LiveContainer
from ai.backend.agent.network.runtime import OciRuntime

__all__ = ("OciRuntimeLocator",)


class OciRuntimeLocator(ContainerLocator):
    """Answers the privnet from an OciRuntime, exposing only the three things it may ask."""

    _runtime: OciRuntime

    def __init__(self, runtime: OciRuntime) -> None:
        self._runtime = runtime

    @override
    async def open(self) -> None:
        await self._runtime.open()

    @override
    async def close(self) -> None:
        await self._runtime.close()

    @override
    async def container_pid(self, container_id: str) -> int | None:
        return await self._runtime.container_pid(container_id)

    @override
    async def live_sessions(self) -> Mapping[str, LiveContainer]:
        live: dict[str, LiveContainer] = {}
        for info in await self._runtime.list_container_infos():
            if session_id := info.labels.get(SESSION_ID_LABEL):
                live[info.id] = LiveContainer(
                    session_id=session_id,
                    owner_agent_id=info.labels.get(OWNER_AGENT_LABEL),
                )
        return live

    @override
    def cgroup_path(self, container_id: str) -> Path:
        # BAI's own layout, which these backends write into their OCI spec's cgroupsPath. The
        # caller has already validated the id; this must never be derived from a request.
        return container_cgroup_fs_path(container_id)
