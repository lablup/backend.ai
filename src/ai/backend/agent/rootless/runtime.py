"""``RootlessOciRuntime`` — what the agent needs from a runtime it does not run as root.

The contract, and only the contract: where this backend keeps its state, which uid the kernel drops
to, where privileged work goes when the agent cannot do it itself, and how a registry's scheme is
decided. Every rootless backend owes the agent these, whoever owns the running container.

That last clause is why this is not :mod:`ai.backend.agent.rootless.base`. enroot and apptainer
have no monitor at all -- the kernel is a child of the agent -- so the agent has to hold the
process, journal its PID, rotate its log and put it in a cgroup itself. That is
``SelfHostedRootlessRuntime``, and it is most of a thousand lines. A rootless runtime that brings
its own monitor (podman's conmon, which reparents the container and keeps its own state, logs and
cgroup) owes the agent exactly the same contract while owning none of that machinery, and
inheriting it would mean turning most of it off.
"""

from __future__ import annotations

import asyncio
import os
from abc import abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

from ai.backend.agent.containerd.runtime.interface import OciRuntime


class RootlessOciRuntime(OciRuntime):
    """The rootless contract. See the module docstring for what is deliberately not here."""

    #: Names this backend in log messages. Subclasses set it.
    backend_name: ClassVar[str] = "rootless"

    _data_path: Path
    _cache_path: Path
    _runtime_path: Path
    # Where this backend keeps what belongs to one container. MUST live outside the runtime's own
    # paths: a runtime that hides its runtime dir inside the container's mount namespace makes a
    # bind source under it invisible ("No such file or directory").
    _state_path: Path
    # When set, privileged work is delegated here: an unprivileged agent can neither create a
    # cgroup nor attach a veth. None = do it locally, which means the agent runs privileged.
    _privnet_socket: str | None
    # The host's containerd `certs.d` tree (`container.registry-hosts-dir`), consulted to decide
    # whether a registry is reached over plain HTTP. None = fall back to the reference heuristic.
    _registry_hosts_dir: Path | None
    # The work-user uid/gid the kernel-runner drops to (LOCAL_USER_ID/GID), from container config.
    _kernel_uid: int
    _kernel_gid: int

    def __init__(
        self,
        *,
        data_path: Path,
        cache_path: Path,
        runtime_path: Path,
        state_path: Path,
        kernel_uid: int,
        kernel_gid: int,
        privnet_socket: str | None = None,
        registry_hosts_dir: Path | None = None,
    ) -> None:
        self._registry_hosts_dir = registry_hosts_dir
        self._data_path = data_path
        self._cache_path = cache_path
        self._runtime_path = runtime_path
        self._state_path = state_path
        self._kernel_uid = kernel_uid
        self._kernel_gid = kernel_gid
        self._privnet_socket = privnet_socket

    @abstractmethod
    def _runtime_env(self) -> dict[str, str]:
        """The runtime's own configuration environment (``ENROOT_*`` / ``APPTAINER_*``)."""
        raise NotImplementedError

    def _process_env(self) -> dict[str, str]:
        # The environment the runtime itself is launched with. A GPU-enabled fatPod sets
        # NVIDIA_VISIBLE_DEVICES=all to get the driver injected into *itself*, and a runtime that
        # forwards its own environment (or a GPU hook that prefers an already-set variable over the
        # container's env file) would then hand every device to every container. Strip NVIDIA_*
        # here so the per-kernel allocation the OCI spec carries is authoritative.
        inherited = {k: v for k, v in os.environ.items() if not k.startswith("NVIDIA_")}
        return {**inherited, **self._runtime_env()}

    def _launch_env(self, spec: Mapping[str, Any]) -> dict[str, str]:
        """The environment for *launching one container*, on top of ``_process_env``.

        A backend whose GPU injection is driven by the **runtime's own** environment rather than by
        the container's needs this seam: `_process_env` deliberately strips ``NVIDIA_*``, which is
        right for a hook that reads the container's env file and wrong for one that reads the
        runtime process's. Empty by default.
        """
        return {}

    def _uid_drop_prefix(self) -> list[str]:
        # Run the runtime **as the kernel uid**, not as the (root) agent — as an argv prefix
        # (`setpriv`) rather than the subprocess user=/group= kwargs, which uvloop (this agent's
        # event loop) does not accept. Dropping to a non-root uid is what makes the runtime install
        # a rootless user namespace, so the container's root IS the kernel uid on the host. The
        # scratch dirs are chowned to the kernel uid, so container-root owns them — everything
        # aligns with no host privilege and no identity-map/`chmod` workaround. No-op when the
        # agent already runs as the kernel uid (a non-privileged deployment). Requires the host
        # prerequisites the krunner entrypoint sets up: /etc/sub{u,g}id for the uid and file caps
        # on newuidmap/newgidmap.
        if os.geteuid() == self._kernel_uid:
            return []
        return [
            "setpriv",
            "--reuid",
            str(self._kernel_uid),
            "--regid",
            str(self._kernel_gid),
            "--init-groups",
        ]

    async def _run(
        self, *argv: str, extra_env: Mapping[str, str] | None = None
    ) -> tuple[int, bytes, bytes]:
        env = {**self._process_env(), **(extra_env or {})}
        proc = await asyncio.create_subprocess_exec(
            *self._uid_drop_prefix(),
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout, stderr

    async def _run_as_agent(self, *argv: str) -> tuple[int, bytes, bytes]:
        """Like ``_run`` but WITHOUT the uid drop — for the few steps that need the agent's own
        privileges (restoring file ownership out of an image archive)."""
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._process_env(),
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout, stderr
