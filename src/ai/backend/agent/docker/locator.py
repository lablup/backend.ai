"""The ContainerLocator for the Docker backend.

Docker answers the same three questions the OCI-spec backends do, just through its own API, so the
privnet drives it without knowing which backend it is talking to. Measured against Docker 29.1.3: a
``--network=none`` container yields a netns holding only ``lo``, ``State.Pid`` resolves it, and a
veth or a vxlan device moved into it by PID carries traffic exactly as it does for containerd.

``cgroup_path`` is deliberately left unimplemented. Docker places its containers itself -- under
``/sys/fs/cgroup/system.slice/docker-<id>.scope`` with the systemd driver, elsewhere with cgroupfs,
and the choice is the daemon's, not ours. Only the rootless backends ask the privnet to create a
cgroup for them; a Docker session that reached that path would have the privnet writing as root to a
path this module guessed.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping
from typing import override

from aiodocker.docker import Docker

from ai.backend.agent.network.locator import (
    OWNER_AGENT_LABEL,
    SESSION_ID_LABEL,
    ContainerLocator,
    LiveContainer,
)

__all__ = ("DockerContainerLocator",)


class DockerContainerLocator(ContainerLocator):
    """Answers the privnet from the Docker daemon."""

    _docker: Docker | None

    def __init__(self) -> None:
        self._docker = None

    @override
    async def open(self) -> None:
        """Connect, and only then let go of whatever was connected before.

        Held for the privnet's lifetime rather than opened per request: the daemon being
        unreachable is a startup fact, and this is the call that surfaces it there.

        Assigning the new client first was the bug: a second `open()` -- which the privnet's entry
        point used to make -- replaced a working client without closing it, leaking its aiohttp
        session over the daemon socket, and a failed re-open left the process holding a client
        that had never answered.
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
            # aiodocker holds an aiohttp session over the daemon's unix socket; dropping it without
            # closing leaks the connector and warns at GC.
            await self._docker.close()
            self._docker = None

    def _client(self) -> Docker:
        if self._docker is None:
            raise RuntimeError("the Docker locator was used before open()")
        return self._docker

    @override
    async def container_pid(self, container_id: str) -> int | None:
        try:
            info = await self._client().containers.container(container_id).show()
        except Exception:
            # Gone between the caller's decision and this call: the caller treats a missing PID as
            # "not running", which is what it is.
            return None
        state = info.get("State") or {}
        if not state.get("Running"):
            return None
        # Docker reports 0 for a container that has no process, not None.
        return pid if (pid := int(state.get("Pid") or 0)) > 0 else None

    @override
    async def live_sessions(self) -> Mapping[str, LiveContainer]:
        live: dict[str, LiveContainer] = {}
        for entry in await self._client().containers.list(all=False):
            # ``list`` already carries the labels, so this stays one API call rather than an inspect
            # per container -- the privnet calls it on every restart and every reconcile.
            labels = entry["Labels"] or {}
            if session_id := labels.get(SESSION_ID_LABEL):
                live[entry.id] = LiveContainer(
                    session_id=session_id,
                    owner_agent_id=labels.get(OWNER_AGENT_LABEL),
                )
        return live
