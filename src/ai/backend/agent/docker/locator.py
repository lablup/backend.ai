"""The ContainerLocator for the Docker backend, answering through the Docker API.

``cgroup_path`` is left unimplemented: the daemon places its own cgroups.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping
from http import HTTPStatus
from typing import override

from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.agent.errors.network import ContainerSourceUnwired
from ai.backend.agent.network.locator import ContainerLocator, LiveContainer
from ai.backend.common.docker import LabelName

__all__ = ("DockerContainerLocator",)


class DockerContainerLocator(ContainerLocator):
    """Answers from the Docker daemon."""

    _docker: Docker | None

    def __init__(self) -> None:
        self._docker = None

    @override
    async def open(self) -> None:
        """Connect, and only then close whatever was connected before.

        Held for the caller's lifetime, so an unreachable daemon surfaces at startup.
        """
        docker = Docker()
        try:
            await docker.version()
        except BaseException:
            await docker.close()
            raise
        previous, self._docker = self._docker, docker
        if previous is not None:
            with contextlib.suppress(Exception):
                await previous.close()

    @override
    async def close(self) -> None:
        if self._docker is not None:
            # Closes aiodocker's aiohttp session; dropping it leaks the connector.
            await self._docker.close()
            self._docker = None

    def _client(self) -> Docker:
        if self._docker is None:
            raise ContainerSourceUnwired("the Docker locator was used before open()")
        return self._docker

    @override
    async def container_pid(self, container_id: str) -> int | None:
        try:
            info = await self._client().containers.container(container_id).show()
        except DockerError as e:
            # Gone since the caller decided. Any other failure is not an answer about the container.
            if e.status == HTTPStatus.NOT_FOUND:
                return None
            raise
        state = info.get("State") or {}
        if not state.get("Running"):
            return None
        # Docker reports 0 for a container that has no process, not None.
        return pid if (pid := int(state.get("Pid") or 0)) > 0 else None

    @override
    async def live_sessions(self) -> Mapping[str, LiveContainer]:
        live: dict[str, LiveContainer] = {}
        for entry in await self._client().containers.list(all=False):
            # ``list`` carries the labels: one API call, no inspect per container.
            labels = entry["Labels"] or {}
            if session_id := labels.get(LabelName.SESSION_ID):
                live[entry.id] = LiveContainer(
                    session_id=session_id,
                    owner_agent_id=labels.get(LabelName.OWNER_AGENT),
                )
        return live
