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
import contextlib
import logging
import os
import time
from abc import abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Final

from ai.backend.agent.containerd.runtime.interface import OciRuntime
from ai.backend.agent.containerd.runtime.spec import container_cgroup_fs_path
from ai.backend.agent.errors.agent import ContainerConfinementFailedError
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# The label the agent stamps on every container; the privnet keys its records by session.
_SESSION_ID_LABEL: Final = "ai.backend.session-id"
# Presence of the unified hierarchy's controller list is what tells cgroup v2 from v1.
_CGROUP_V2_MARKER: Final = "/sys/fs/cgroup/cgroup.controllers"
# rmdir on a cgroup whose members are still exiting returns EBUSY; ~1s total is far more than the
# kernel needs to reap processes that have already been SIGKILLed.
_CGROUP_RMDIR_RETRIES: Final = 20
_CGROUP_RMDIR_DELAY_SEC: Final = 0.05


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
    # container_id -> the OCI spec's labels (KERNEL_ID_LABEL/OWNER_AGENT_LABEL/...). The agent
    # filters on these to reconcile live kernels and rebuild the resource alloc map, so an empty
    # set here would drop every container from reconstruct_resource_usage; the cgroup work below
    # also reads the session id out of them.
    _labels: dict[str, Mapping[str, str]]

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
        self._labels = {}

    # ------------------------------------------------------------------ cgroup confinement
    async def _release_via_privnet(self, container_id: str) -> None:
        from ai.backend.agent.network.privnet.client import PrivNetClient, PrivNetClientError

        session_id = str(self._labels.get(container_id, {}).get(_SESSION_ID_LABEL, container_id))
        try:
            await PrivNetClient(self._privnet_socket or "").release_container(
                session_id, container_id
            )
        except (OSError, TimeoutError, PrivNetClientError) as e:
            log.warning(
                "[{}] privnet could not release the cgroup for {}: {!r}",
                self.backend_name,
                container_id,
                e,
            )

    async def _confine_via_privnet(
        self, container_id: str, spec: Mapping[str, Any], top_pid: int
    ) -> None:
        """Have the privnet create this container's cgroup and move its tree in.

        These runtimes have no daemon of their own and an unprivileged agent cannot make a cgroup
        under /sys/fs/cgroup, so there is nobody else to ask. containerd and dockerd get this for
        free: they declare `cgroupsPath` in the OCI spec and their ROOT daemon obliges. Without the
        delegation the kernel simply stays in the agent's own cgroup — measured on a kernel
        allocated 8 GiB and 4 CPUs: `memory.max = max`, `Cpus_allowed_list: 0-31`.

        A failure here fails the creation. It used to warn and start the kernel anyway, and what
        that produced is not a degraded kernel but a dishonest one: the manager placed it on this
        node believing its limits hold, and it has none of them. There is no fallback to try — the
        local path cannot work either, which is why we are here — and the caller is still holding
        the container at its gate, so nothing of the user's command has run yet.

        The narrow except is deliberate. A bare `Exception` here also swallowed programming errors
        in this method — a typo in `_cgroup_limits` surfaced as "privnet could not confine" and
        silently disabled every limit on the node — so only the ways the privnet itself can fail
        are caught.
        """
        from ai.backend.agent.network.privnet.client import PrivNetClient, PrivNetClientError

        session_id = str(self._labels.get(container_id, {}).get(_SESSION_ID_LABEL, container_id))
        try:
            await PrivNetClient(self._privnet_socket or "").confine_container(
                session_id, container_id, top_pid, self._cgroup_limits(spec)
            )
        except (OSError, TimeoutError, PrivNetClientError) as e:
            raise ContainerConfinementFailedError(
                f"the privnet could not confine {container_id} ({e!r}); refusing to start a kernel"
                " that would run without the CPU and memory it was allocated"
            ) from e

    def _create_cgroup(self, container_id: str, spec: Mapping[str, Any]) -> Path | None:
        """Create the kernel's cgroup and write its limits. None when this host cannot do it."""
        if not Path(_CGROUP_V2_MARKER).exists():
            # cgroup v1 splits every controller into its own hierarchy; the agent's stats reader
            # composes those per-controller mount points itself. Rather than half-apply limits
            # across trees, say plainly that this host gets none.
            log.warning(
                "[{}] cgroup v1 host: per-kernel CPU/memory limits and stats are NOT applied",
                self.backend_name,
            )
            return None
        cgroup = container_cgroup_fs_path(container_id)
        parent = cgroup.parent
        try:
            parent.mkdir(parents=True, exist_ok=True)
            # A controller only reaches a child if the parent delegates it. Without this the leaf
            # has no cpuset.cpus / memory.max files to write at all. `io` is not something we set,
            # but the memory plugin reads `io.stat` on every pass and an undelegated controller
            # means that file does not exist — which is a FileNotFoundError, i.e. no memory
            # measurement either.
            (parent / "cgroup.subtree_control").write_text("+cpu +cpuset +io +memory")
            cgroup.mkdir(exist_ok=True)
        except OSError as e:
            raise ContainerConfinementFailedError(
                f"cannot create the cgroup {cgroup} ({e!r}); refusing to start a kernel that would"
                " run without the CPU and memory it was allocated"
            ) from e
        self._write_cgroup_limits(cgroup, spec)
        return cgroup

    @staticmethod
    def _cgroup_limits(spec: Mapping[str, Any]) -> dict[str, str]:
        """The cgroup interface files this spec asks for. Split out so the privnet delegation and
        the local writer send the same numbers."""
        limits: list[tuple[str, str]] = []
        if cpus := spec.get("cpuset_cpus"):
            limits.append(("cpuset.cpus", str(cpus)))
        if mems := spec.get("cpuset_mems"):
            limits.append(("cpuset.mems", str(mems)))
        memory_limit = spec.get("memory_limit")
        if memory_limit is not None:
            limits.append(("memory.max", str(int(memory_limit))))
        memory_swap = spec.get("memory_swap")
        if memory_swap is not None and memory_limit is not None:
            # OCI (and Docker) count `memory_swap` as memory+swap combined; cgroup v2's
            # memory.swap.max is swap ALONE. Writing the combined figure would silently grant the
            # container its whole memory limit again as swap.
            limits.append(("memory.swap.max", str(max(0, int(memory_swap) - int(memory_limit)))))
        return dict(limits)

    @staticmethod
    def _write_cgroup_limits(cgroup: Path, spec: Mapping[str, Any]) -> None:
        """Apply every limit, or fail saying which ones did not take.

        Per-file, because a partial apply is the worst of the three outcomes: the kernel looks
        confined and is not, in whichever dimension failed. The privnet's own `_make_cgroup` already
        collects its failures and raises; this is the same rule on the local path.
        """
        failed: list[str] = []
        for name, value in RootlessOciRuntime._cgroup_limits(spec).items():
            try:
                (cgroup / name).write_text(value)
            except OSError as e:
                log.warning("cannot set {}={} on {}: {!r}", name, value, cgroup, e)
                failed.append(f"{name}={value} ({e.__class__.__name__})")
        if failed:
            raise ContainerConfinementFailedError(
                f"these limits could not be applied to {cgroup}: {', '.join(failed)}"
            )

    def _remove_cgroup(self, container_id: str) -> None:
        """Reclaim the kernel's cgroup once its processes are gone.

        An empty cgroup is only a directory, but they are never reused (the name is the kernel id),
        so leaving them accumulates one per kernel this node has ever run.

        rmdir fails with EBUSY while *any* member is still exiting, and the caller has just killed
        them — a single attempt loses that race and leaks the directory (measured). `cgroup.kill`
        is the v2 way to make that deterministic: it SIGKILLs every remaining member at once, and
        the short retry then only has to outlast the kernel reaping them.
        """
        cgroup = container_cgroup_fs_path(container_id)
        if not cgroup.exists():
            return
        with contextlib.suppress(OSError):
            (cgroup / "cgroup.kill").write_text("1")
        for _ in range(_CGROUP_RMDIR_RETRIES):
            try:
                cgroup.rmdir()
                return
            except FileNotFoundError:
                return
            except OSError:
                time.sleep(_CGROUP_RMDIR_DELAY_SEC)
        log.warning(
            "[{}] could not reclaim the cgroup {}; it will be left behind",
            self.backend_name,
            cgroup,
        )

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
