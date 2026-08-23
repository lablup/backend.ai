"""``RootlessOciRuntime`` — everything a daemonless rootless runtime owes the agent.

The containerd backend gets a great deal for free from its daemon: cgroups, a container list that
survives an agent restart, a log driver with rotation, an event stream for container death. enroot
and singularity have no daemon, so each of them would otherwise have to provide all of it — and
none of it depends on how the image is stored or how the runtime binary is spelled.

So it lives here once, and a backend subclasses this and supplies only what genuinely differs:

* ``_runtime_env`` — the runtime's own configuration environment (``ENROOT_*`` / ``APPTAINER_*``).
* ``_launch_argv`` — the command line that starts one container, running the pause wrapper.
* ``_discard_container`` — dropping the runtime's own record of a container, on removal.
* the image surface (``pull_image`` / ``commit_container`` / ``push_image`` / ...), which is where
  a squashfs archive and a sandbox directory genuinely part ways.

**The two-phase gate** is the load-bearing shared piece. The agent's attach sequence is

    handle = await runtime.create_task(cid)   # netns exists, user command NOT exec'd
    await network.attach(..., task_pid=handle.pid)
    await runtime.start_task(cid)             # release the gate -> exec

which neither runtime has natively — both exec immediately. It is emulated with a small wrapper
that enters the namespaces, signals readiness, blocks on a FIFO, then ``exec``s the real command,
preserving the PID the network layer attached to. That is the entire runtime-specific contract for
BEP-1062: *produce an attachable netns and a stable PID*.
"""

from __future__ import annotations

import asyncio
import contextlib
import gzip
import hashlib
import json
import logging
import os
import shutil
import tarfile
import time
from abc import abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path
from typing import IO, Any, ClassVar, Final, cast, override

import ai.backend.agent.rootless.seccomp_installer
from ai.backend.agent.containerd.log_writer import (
    LOG_FILE_COUNT,
    max_file_size,
    rotated_path,
)
from ai.backend.agent.containerd.logs import unlink_log_files
from ai.backend.agent.containerd.runtime.interface import (
    ContainerInfo,
    ExecResult,
    OciRuntime,
    TaskEvent,
    TaskHandle,
)
from ai.backend.agent.containerd.runtime.spec import container_cgroup_fs_path
from ai.backend.agent.network.journal_io import atomic_write
from ai.backend.agent.rootless.seccomp import compile_profile
from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

# The per-container gate directory (pause script + go FIFO) is bind-mounted here inside the
# container; a top-level hidden path avoids colliding with the image / OCI-spec mounts.
GATE_MNT: Final = "/.bai-rootless-gate"
# The seccomp filter the agent compiled for this container, and the installer that puts it on.
# Both are bind-mounted in with the gate.
SECCOMP_FILTER: Final = "seccomp.bpf"
SECCOMP_INSTALLER: Final = "seccomp_installer.py"
# Shipped beside the compiler that produces the filter it installs, not with any one backend.
_SECCOMP_INSTALLER_SRC: Final = Path(ai.backend.agent.rootless.seccomp_installer.__file__).resolve()
# The interpreter the krunner mount always provides; the image's own python may not exist.
_KRUNNER_PYTHON: Final = "/opt/backend.ai/bin/python"
# The two-phase pause. It (1) writes a `ready` marker so create_task knows the wrapper — not a
# transient runtime setup process — is the stable netns holder, then (2) blocks in the shell itself
# (`read`, no child `cat`) opening the go FIFO, so this exact PID is what create_task attaches to;
# on go it `exec`s the real command, preserving that PID.
PAUSE_SCRIPT: Final = f"""#!/bin/sh
: > {GATE_MNT}/ready
read _ < {GATE_MNT}/go 2>/dev/null
if [ -f {GATE_MNT}/{SECCOMP_FILTER} ]; then
  exec {_KRUNNER_PYTHON} {GATE_MNT}/{SECCOMP_INSTALLER} {GATE_MNT}/{SECCOMP_FILTER} "$@"
fi
exec "$@"
"""
# OCI mount types a userns runtime provides itself — never forwarded as host binds.
SKIP_MOUNT_TYPES: Final = frozenset({
    "proc",
    "sysfs",
    "tmpfs",
    "cgroup",
    "cgroup2",
    "mqueue",
    "devpts",
    "devtmpfs",
})
# Docker's default ShmSize, used when the session did not ask for one.
DEFAULT_SHM_BYTES: Final = 64 * 1024 * 1024
# How long create_task waits for the container to reach its netns'd pause.
TASK_START_TIMEOUT_SEC: Final = 30.0
# Neither runtime has an event stream, so container death is polled for.
TASK_POLL_INTERVAL_SEC: Final = 1.0
# How often each live container's log is measured against the cap. A stat() per container is
# nothing, and the interval is what bounds the overshoot (see _rotate_logs_loop).
LOG_ROTATE_INTERVAL_SEC: Final = 5.0
_LOG_COPY_CHUNK: Final = 1024 * 1024
# Presence of the unified hierarchy's controller list is what tells cgroup v2 from v1.
_CGROUP_V2_MARKER: Final = "/sys/fs/cgroup/cgroup.controllers"
# rmdir on a cgroup whose members are still exiting returns EBUSY; ~1s total is far more than the
# kernel needs to reap processes that have already been SIGKILLed.
_CGROUP_RMDIR_RETRIES: Final = 20
_CGROUP_RMDIR_DELAY_SEC: Final = 0.05


class _HashingWriter:
    """Pass-through writer that digests everything written to it."""

    def __init__(self, stream: Any, digest: Any) -> None:
        self._stream = stream
        self._digest = digest

    def write(self, data: bytes) -> int:
        self._digest.update(data)
        return int(self._stream.write(data))


def write_layer(rootfs: Path, layer_path: Path) -> str:
    """Tar+gzip ``rootfs`` into ``layer_path``; return the tar's UNCOMPRESSED sha256.

    That digest is the config's ``rootfs.diff_ids`` entry, and it has to be taken as the tar is
    produced — recomputing it later would mean decompressing the whole layer again.

    ``mtime=0`` and an empty ``filename`` on the gzip wrapper keep the layer byte-identical across
    runs of the same rootfs, so re-pushing an unchanged image is a no-op the registry can dedupe.
    Both are needed: gzip stores an mtime *and* an originating filename, and GzipFile takes the
    latter from ``fileobj.name`` unless told otherwise — which would put the agent's scratch path
    in the blob and change its digest.
    """
    diff = hashlib.sha256()
    with layer_path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as gz:
            # Stream mode ("w|") only ever calls write() on the fileobj, which is all
            # _HashingWriter provides.
            sink = cast(IO[bytes], _HashingWriter(gz, diff))
            with tarfile.open(fileobj=sink, mode="w|") as tar:
                tar.add(rootfs, arcname=".", recursive=True)
    return f"sha256:{diff.hexdigest()}"


def force_rmtree(path: Path) -> None:
    """``rmtree`` that also removes directories it cannot descend into.

    overlayfs creates its own ``work/work`` with mode ``0000``, and ``shutil.rmtree`` cannot
    scandir that even when it owns it — so a plain ``ignore_errors=True`` silently leaves the whole
    tree behind (measured end-to-end: every container leaked its overlay, holding everything it had
    written). We own these paths, so restore traversal permission on the way down and then remove.

    Retrying from ``rmtree``'s own error hook is not an option: its fd-based implementation hands
    the hook ``os.open``, which cannot be re-invoked with a path alone.

    Whatever survives is swallowed, matching the ``ignore_errors=True`` this replaces — a reclaim
    that cannot finish must not take down the teardown around it.
    """
    if not path.exists():
        return
    # topdown, so each directory is made traversable before the walk tries to descend into it.
    for parent, dirnames, _ in os.walk(path, topdown=True, onerror=lambda _e: None):
        for dirname in dirnames:
            with contextlib.suppress(OSError):
                Path(parent, dirname).chmod(0o700)
    shutil.rmtree(path, ignore_errors=True)


class RootlessOciRuntime(OciRuntime):
    """Shared implementation for the daemonless rootless backends. See the module docstring."""

    #: Names this backend in log messages. Subclasses set it.
    backend_name: ClassVar[str] = "rootless"

    _data_path: Path
    _cache_path: Path
    _runtime_path: Path
    # Gate dirs (pause script + go FIFO) and container logs. MUST live outside the runtime's own
    # paths: a runtime that hides its runtime dir inside the container's mount ns makes a bind
    # source under it invisible ("No such file or directory").
    _state_path: Path
    # oci_spec handed in at create_container, kept until the task is built (consumed as
    # mounts/env/hooks, not as a spec file).
    _specs: dict[str, Mapping[str, Any]]
    # container_id -> the real command (kernel entrypoint + args) to exec after the gate opens.
    _commands: dict[str, Sequence[str]]
    # container_id -> netns-holder host PID (the container's stable PID), for netns attach + kill.
    _pids: dict[str, int]
    # container_id -> the top launch subprocess (owns the process tree; awaited on exit).
    _procs: dict[str, asyncio.subprocess.Process]
    # container_id -> source image ref, so remove/commit can find the image.
    _images: dict[str, str]
    # container_id -> the OCI spec's labels (KERNEL_ID_LABEL/OWNER_AGENT_LABEL/...). enumerate_
    # containers filters on these to reconcile live kernels + rebuild the resource alloc map, so an
    # empty set here would drop every container from reconstruct_resource_usage.
    _labels: dict[str, Mapping[str, str]]
    _log_root: Path | None
    # container_logs.max_length: the total budget across the active log and its rotated siblings.
    # 0 until configure_logging() runs (which is after open()), meaning "not configured, do not
    # rotate" rather than "rotate at zero bytes".
    _log_max_bytes: int
    # The periodic in-place rotation task; see _rotate_logs_loop.
    _rotator_task: asyncio.Task[None] | None
    # This agent's own netns inode, to tell the container's dedicated netns apart from ours.
    _agent_netns: int | None
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
    ) -> None:
        self._data_path = data_path
        self._cache_path = cache_path
        self._runtime_path = runtime_path
        self._state_path = state_path
        self._kernel_uid = kernel_uid
        self._kernel_gid = kernel_gid
        self._specs = {}
        self._commands = {}
        self._pids = {}
        self._procs = {}
        self._images = {}
        self._labels = {}
        self._log_root = None
        self._log_max_bytes = 0
        self._rotator_task = None
        self._agent_netns = None

    # ------------------------------------------------------------------ backend hooks
    @abstractmethod
    def _runtime_env(self) -> dict[str, str]:
        """The runtime's own configuration environment (``ENROOT_*`` / ``APPTAINER_*``)."""
        raise NotImplementedError

    @abstractmethod
    def _launch_argv(self, container_id: str, spec: Mapping[str, Any], gate_dir: Path) -> list[str]:
        """The command line that starts one container with the pause wrapper as its command."""
        raise NotImplementedError

    @abstractmethod
    async def _discard_container(self, container_id: str) -> None:
        """Drop the runtime's own record/rootfs of a container. Called by remove_container."""
        raise NotImplementedError

    def _own_existing_artifacts(self) -> None:
        """Hand artifacts an earlier, differently-privileged run left behind to the kernel uid.

        Default: nothing to do. A backend whose image tooling used to run as root overrides this.
        """

    # ------------------------------------------------------------------ lifecycle
    @override
    async def open(self) -> None:
        # The runtime runs as the kernel uid (rootless; see _uid_drop_prefix), so its data/cache/
        # runtime and the per-container state (gate/logs) must be owned by that uid, not root. Hand
        # over the roots; per-container children inherit via the kernel-uid-run runtime /
        # _write_gate. No-op when the agent already runs as the kernel uid.
        own = os.geteuid() != self._kernel_uid
        for p in (self._data_path, self._cache_path, self._runtime_path, self._state_path):
            p.mkdir(parents=True, exist_ok=True)
            if own:
                os.chown(p, self._kernel_uid, self._kernel_gid)
        if own:
            await asyncio.to_thread(self._own_existing_artifacts)
        await asyncio.to_thread(self._recover_containers)
        await asyncio.to_thread(self._sweep_orphan_cgroups)
        if self._rotator_task is None:
            self._rotator_task = asyncio.create_task(self._rotate_logs_loop())

    @override
    async def close(self) -> None:
        if self._rotator_task is not None:
            self._rotator_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._rotator_task
            self._rotator_task = None

    # ------------------------------------------------------------------ subprocess plumbing
    def _process_env(self) -> dict[str, str]:
        # The environment the runtime itself is launched with. A GPU-enabled fatPod sets
        # NVIDIA_VISIBLE_DEVICES=all to get the driver injected into *itself*, and a runtime that
        # forwards its own environment (or a GPU hook that prefers an already-set variable over the
        # container's env file) would then hand every device to every container. Strip NVIDIA_*
        # here so the per-kernel allocation the OCI spec carries is authoritative.
        inherited = {k: v for k, v in os.environ.items() if not k.startswith("NVIDIA_")}
        return {**inherited, **self._runtime_env()}

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

    # ------------------------------------------------------------------ container lifecycle
    @override
    async def create_task(self, container_id: str, *, use_logger: bool = True) -> TaskHandle:
        # Two-phase emulation (see module docstring). Launch the runtime with a dedicated netns and
        # PID ns, running the pause-wrapper as the command: the container comes up, enters its own
        # netns, and BLOCKS before exec'ing the real command. Its host PID (the netns holder) is
        # returned so the network layer can attach veth to /proc/<pid>/ns/net; start_task then opens
        # the go FIFO to resume it. The wrapper's `exec` preserves this PID across the resume.
        spec = self._specs[container_id]
        gate_dir = self._gate_dir(container_id)
        await asyncio.to_thread(self._write_gate, gate_dir)
        await asyncio.to_thread(self._write_seccomp, gate_dir, spec)
        argv = self._launch_argv(container_id, spec, gate_dir)
        log.debug("[{}] launch argv: {}", self.backend_name, " ".join(argv))
        log_fd = self._open_log(container_id)
        try:
            proc = await asyncio.create_subprocess_exec(
                *self._uid_drop_prefix(),
                *argv,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=log_fd,
                stderr=log_fd,
                env=self._process_env(),
            )
        finally:
            os.close(log_fd)
        self._procs[container_id] = proc
        try:
            await self._wait_ready(proc, gate_dir)
            pid = await self._find_netns_child(proc)
        except BaseException:
            await self._reap(container_id)
            raise
        self._pids[container_id] = pid
        await asyncio.to_thread(self._record_container, container_id, pid)
        await self._set_hostname(pid, spec.get("hostname"))
        # Confine the container now, while the wrapper is still blocked on the gate: every process
        # that will run the user's command is already forked, and none of it has started. Doing it
        # after start_task would let the workload run unconfined for however long the move takes.
        await asyncio.to_thread(self._confine, container_id, spec, proc.pid)
        return TaskHandle(container_id=container_id, pid=pid)

    @override
    async def start_task(self, container_id: str) -> None:
        # Open the go FIFO for writing — the paused wrapper already holds the read end open, so this
        # does not block — and write, releasing the wrapper to exec the real command into the netns
        # the network layer has now populated.
        go_fifo = self._gate_dir(container_id) / "go"
        await asyncio.to_thread(self._signal_go, go_fifo)

    @override
    async def kill_container(
        self, container_id: str, *, signal: int, all_processes: bool = True
    ) -> None:
        pid = self._pids.get(container_id)
        if pid is None:
            return
        # all_processes -> signal the process group (the launch tree); else the init PID only.
        target = -pid if all_processes else pid
        try:
            os.kill(target, signal)
        except ProcessLookupError:
            pass

    @override
    async def stop_container(self, container_id: str, *, grace_period: float) -> None:
        # SIGTERM the init, poll (a raw PID has no awaitable) up to grace_period, then SIGKILL.
        await self.kill_container(container_id, signal=15, all_processes=False)
        poll_interval = 0.2
        for _ in range(max(1, int(grace_period / poll_interval))):
            if await self.container_status(container_id) in (None, "stopped"):
                return
            await asyncio.sleep(poll_interval)
        await self.kill_container(container_id, signal=9, all_processes=True)

    @override
    async def remove_container(self, container_id: str) -> None:
        await self.kill_container(container_id, signal=9, all_processes=True)
        await self._reap(container_id)
        await self._discard_container(container_id)
        # The log is as much part of the container as its rootfs — the containerd runtime unlinks it
        # here too. The rotated siblings go with it: leaving them would keep a terminated kernel's
        # log on disk forever, since nothing else ever revisits that path.
        await asyncio.to_thread(unlink_log_files, self._log_path(container_id))
        # ...and the two-phase gate (pause.sh + the `go` FIFO) under the per-container state dir.
        await asyncio.to_thread(force_rmtree, self._state_path / container_id)
        await asyncio.to_thread(self._remove_cgroup, container_id)
        self._specs.pop(container_id, None)
        self._commands.pop(container_id, None)
        self._pids.pop(container_id, None)
        self._images.pop(container_id, None)
        self._labels.pop(container_id, None)

    async def _reap(self, container_id: str) -> None:
        proc = self._procs.pop(container_id, None)
        if proc is not None and proc.returncode is None:
            proc.kill()
            await proc.wait()

    # ------------------------------------------------------------------ the two-phase gate
    def _gate_dir(self, container_id: str) -> Path:
        return self._state_path / container_id / "gate"

    def _write_gate(self, gate_dir: Path) -> None:
        gate_dir.mkdir(parents=True, exist_ok=True)
        script = gate_dir / "pause.sh"
        script.write_text(PAUSE_SCRIPT)
        script.chmod(0o755)
        fifo = gate_dir / "go"
        if not fifo.exists():
            os.mkfifo(fifo, 0o600)
        # The container runs as the kernel uid, so it — not the root agent — is what writes the
        # `ready` marker into the gate dir and reads the `go` FIFO. Hand the gate (and its parent,
        # the per-container state dir) to the kernel uid so those cross into the container. No-op
        # when the agent already runs as the kernel uid.
        if os.geteuid() != self._kernel_uid:
            os.chown(gate_dir.parent, self._kernel_uid, self._kernel_gid)
            os.chown(gate_dir, self._kernel_uid, self._kernel_gid)
            os.chown(script, self._kernel_uid, self._kernel_gid)
            os.chown(fifo, self._kernel_uid, self._kernel_gid)

    def _write_seccomp(self, gate_dir: Path, spec: Mapping[str, Any]) -> None:
        """Compile this container's seccomp profile into the gate, for the pause wrapper to apply.

        Absent profile means the operator chose the jail sandbox (the agent then does not generate
        one) — that is a deliberate posture, not a failure, so there is simply no filter to install.
        A profile that is present but will not compile IS a failure: starting the container anyway
        would silently run it unconfined.
        """
        oci_seccomp = spec.get("seccomp")
        if not oci_seccomp:
            return
        program = compile_profile(oci_seccomp, arch=CURRENT_ARCH)
        (gate_dir / SECCOMP_FILTER).write_bytes(program)
        shutil.copyfile(_SECCOMP_INSTALLER_SRC, gate_dir / SECCOMP_INSTALLER)
        log.debug(
            "[{}] seccomp: {} instructions for {}",
            self.backend_name,
            len(program) // 8,
            CURRENT_ARCH,
        )

    async def _wait_ready(self, proc: asyncio.subprocess.Process, gate_dir: Path) -> None:
        # Wait until the pause-wrapper writes its `ready` marker (it has reached the FIFO pause and
        # is the stable netns holder) before attaching — avoids racing a transient setup PID.
        ready = gate_dir / "ready"
        poll = 0.1
        for _ in range(max(1, int(TASK_START_TIMEOUT_SEC / poll))):
            if ready.exists():
                return
            if proc.returncode is not None:
                raise RuntimeError(
                    f"{self.backend_name} launch exited before pause (rc={proc.returncode})"
                )
            await asyncio.sleep(poll)
        raise TimeoutError(
            f"{self.backend_name} container did not reach the pause (no ready marker)"
        )

    def _signal_go(self, go_fifo: Path) -> None:
        with go_fifo.open("w") as f:
            f.write("go\n")

    def _log_hardening_disposition(self, container_id: str, spec: Mapping[str, Any]) -> None:
        # Make the hardening model explicit and observable. Capabilities and AppArmor are dropped
        # by design (the userns scopes caps; neither runtime has AppArmor integration). Syscall
        # filtering comes from the compiled seccomp filter above, or — when the operator picked the
        # jail sandbox and so no profile was generated — from jail alone.
        if not spec.get("seccomp"):
            log.info(
                "[{}] no seccomp profile for container {} — syscall filtering comes from the "
                "jail sandbox alone (sandbox_type=jail)",
                self.backend_name,
                container_id,
            )

    async def _set_hostname(self, pid: int, hostname: str | None) -> None:
        """Give the container its cluster hostname (`main1`, `sub1`, ...).

        runc applies the OCI spec's hostname; these runtimes have no equivalent and a fresh UTS
        namespace just inherits the agent's, so without this every kernel calls itself by the agent
        pod's name — wrong for anything that treats the hostname as its cluster identity (MPI, some
        torch-distributed setups). Set from outside, entering the container's user namespace as its
        owner so this works whether the agent runs as root or already as the kernel uid.
        """
        if not hostname:
            return
        rc, _out, err = await self._run(
            "nsenter",
            "-t",
            str(pid),
            "-U",
            "-u",
            "--preserve-credentials",
            "--",
            "hostname",
            hostname,
        )
        if rc != 0:
            log.warning(
                "[{}] could not set the hostname of pid {} to {}: {}",
                self.backend_name,
                pid,
                hostname,
                err.decode(errors="replace").strip(),
            )

    # ------------------------------------------------------------------ container journal
    def _meta_path(self, container_id: str) -> Path:
        # Beside the gate, under the per-container state dir, so remove_container's rmtree already
        # takes the journal entry with it.
        return self._state_path / container_id / "container.json"

    def _record_container(self, container_id: str, pid: int) -> None:
        """Journal what a restart needs to find this container again.

        These runtimes have no daemon and no label store: their own container lists know names, not
        our kernel labels, and nothing on the host maps a container to its netns-holder PID.
        Without this the runtime's knowledge of running containers is process memory, and an agent
        worker restart — which the containers *survive*, being reparented to the pod's supervisor —
        leaves the fresh runtime reporting none of them. reconstruct_resource_usage would then free
        every slot and the orphan-kernel sweep could kill live kernels.
        """
        meta = {
            "pid": pid,
            "start_time": self._pid_start_time(pid),
            "image": self._images.get(container_id, ""),
            "labels": dict(self._labels.get(container_id, {})),
        }
        path = self._meta_path(container_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, json.dumps(meta))

    def _recover_containers(self) -> None:
        """Rebuild the in-memory container tables from the journal, dropping what is no longer live."""
        if not self._state_path.is_dir():
            return
        for entry in self._state_path.iterdir():
            path = entry / "container.json"
            try:
                meta = json.loads(path.read_text())
            except FileNotFoundError:
                continue
            except (OSError, ValueError) as e:
                log.warning(
                    "[{}] unreadable container journal {}: {!r}", self.backend_name, path, e
                )
                continue
            pid = meta.get("pid")
            if not isinstance(pid, int):
                continue
            # The PID must still be the same *live* process: not exited, not a zombie, and not a
            # reused number (which is what the start time rules out).
            if not self._alive(pid) or self._pid_start_time(pid) != meta.get("start_time"):
                log.debug("[{}] journal entry {} is stale; dropping", self.backend_name, entry.name)
                shutil.rmtree(entry, ignore_errors=True)
                continue
            self._pids[entry.name] = pid
            self._images[entry.name] = str(meta.get("image") or "")
            self._labels[entry.name] = dict(meta.get("labels") or {})
        if self._pids:
            log.info(
                "[{}] recovered {} running container(s) from the journal",
                self.backend_name,
                len(self._pids),
            )

    # ------------------------------------------------------------------ cgroup confinement
    def _confine(self, container_id: str, spec: Mapping[str, Any], top_pid: int) -> None:
        """Put the container's whole process tree in its own cgroup, with the allocated limits.

        runc does this from the OCI spec's ``linux.resources`` + ``cgroupsPath``; these runtimes
        have no cgroup integration at all, so without this the container simply inherits the
        agent's cgroup — meaning a kernel allocated 2 CPUs can saturate the node, and the agent's
        stats reader finds nothing at the path it expects
        (``/sys/fs/cgroup/backend-ai/<kernel-id>``), so every kernel reports no CPU or memory
        utilization at all. Both are the same missing cgroup.

        The path comes from the containerd backend's own helper, so the reader and this writer
        cannot disagree about where a kernel's cgroup lives.
        """
        cgroup = self._create_cgroup(container_id, spec)
        if cgroup is None:
            return
        # Move the top process and everything under it. The netns holder — the process that will
        # exec the user command — is in there, and children inherit the cgroup, so the workload and
        # anything it spawns stay confined.
        for pid in (top_pid, *self._descendant_pids(top_pid)):
            try:
                (cgroup / "cgroup.procs").write_text(str(pid))
            except ProcessLookupError:
                continue  # a transient setup process that already exited
            except OSError as e:
                log.warning(
                    "[{}] cannot move pid {} into {}: {!r}", self.backend_name, pid, cgroup, e
                )

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
            log.warning("[{}] cannot create the cgroup {}: {!r}", self.backend_name, cgroup, e)
            return None
        self._write_cgroup_limits(cgroup, spec)
        return cgroup

    @staticmethod
    def _write_cgroup_limits(cgroup: Path, spec: Mapping[str, Any]) -> None:
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
        for name, value in limits:
            try:
                (cgroup / name).write_text(value)
            except OSError as e:
                log.warning("cannot set {}={} on {}: {!r}", name, value, cgroup, e)

    def _sweep_orphan_cgroups(self) -> None:
        """Reclaim kernel cgroups left behind by an agent that died before it could clean up.

        remove_container normally reclaims them, but it only runs when the agent is alive to run
        it: kill the agent mid-session and the cgroup outlives both the container and the process
        that made it. Nothing else ever revisits that path, so they accumulate one per kernel the
        node lost that way. Runs after the journal replay, so a cgroup whose container we just
        recovered is populated and therefore skipped — only genuinely empty ones are removed.
        """
        parent = container_cgroup_fs_path("_").parent
        if not parent.is_dir():
            return
        removed = 0
        for cgroup in parent.iterdir():
            if not cgroup.is_dir() or cgroup.name in self._pids:
                continue
            try:
                if (cgroup / "cgroup.procs").read_text().strip():
                    continue  # something is still running in it; not ours to reap
                cgroup.rmdir()
                removed += 1
            except OSError:
                continue
        if removed:
            log.info("[{}] reclaimed {} orphaned kernel cgroup(s)", self.backend_name, removed)

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

    # ------------------------------------------------------------------ logs
    @override
    def configure_logging(self, launcher: Path, log_root: Path, max_total_bytes: int) -> None:
        # Neither runtime has a log driver: they exec the command with the invoker's stdio
        # inherited (the HPC model is that the caller — Slurm, usually — owns redirection). So the
        # `launcher` (containerd's binary:// writer, which containerd itself starts and which owns
        # the write end) has nobody to start it here; the container writes straight to our file
        # descriptor instead, and the size cap has to be enforced from the outside. See
        # _rotate_logs_loop.
        self._log_root = log_root
        self._log_max_bytes = max_total_bytes

    def _log_path(self, container_id: str) -> Path:
        # The path the agent's reader expects (containerd.runtime.grpc.container_log_path); it must
        # stay in step with it, so the log root is whatever configure_logging was handed.
        if self._log_root is not None:
            return self._log_root / f"{container_id}.log"
        return self._state_path / container_id / "container.log"

    def _open_log(self, container_id: str) -> int:
        # No binary:// log launcher; capture the container's stdio to a file the agent can tail
        # (get_logs). Returns an fd handed to the subprocess; the caller closes its copy. O_APPEND
        # is what makes the out-of-band rotation in _rotate_log() safe.
        path = self._log_path(container_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

    async def _rotate_logs_loop(self) -> None:
        """Cap each live container's log the way the containerd log writer does.

        containerd gets a hard cap for free: it starts our `binary://` writer, which owns the write
        end and simply opens a new file when the active one is full. These runtimes have no
        equivalent — the container holds our file descriptor for its whole life — so the cap has to
        be applied from outside, by watching the file and rotating it underneath the writer.

        That makes the cap a *soft* one: the log can overshoot by whatever the container writes
        between two checks. The alternative — handing the container a pipe and reading it here —
        buys a hard cap at the price of blocking the container's stdout whenever the reader is gone,
        and kernels are meant to outlive an agent restart. An overshooting log file is recoverable;
        a kernel wedged on a full pipe is not.
        """
        while True:
            await asyncio.sleep(LOG_ROTATE_INTERVAL_SEC)
            # 0 until configure_logging runs; None until then too. Nothing to cap yet.
            if self._log_max_bytes <= 0 or self._log_root is None:
                continue
            # Driven by what is on disk, not by self._pids: a kernel recovered after an agent
            # restart never went through create_task, so it has no entry there — and it is exactly
            # the long-lived kernel whose log needs capping most. A log with no writer left just
            # falls under the threshold and is skipped.
            try:
                actives = await asyncio.to_thread(sorted, self._log_root.glob("*.log"))
            except OSError as e:
                log.warning("[{}] cannot list the container log root: {!r}", self.backend_name, e)
                continue
            for active in actives:
                try:
                    await asyncio.to_thread(self._rotate_log, active, self._log_max_bytes)
                except Exception:
                    log.exception("[{}] rotating {} failed", self.backend_name, active)

    @staticmethod
    def _rotate_log(active: Path, max_total_bytes: int) -> None:
        """Roll `active` over into `.1` once it fills, keeping the containerd file layout.

        The container is writing to this exact inode and will keep doing so, which rules out the
        usual rename-and-reopen: renaming would leave it appending to a file nobody reads. So the
        active file is rotated *in place* — its contents are copied out to `.1`, then it is
        truncated to zero. The container's descriptor is O_APPEND, so its next write lands at the
        new end of file and the log continues seamlessly.

        The one thing this cannot do that a writer-owned rotation can: bytes appended between the
        copy and the truncate are dropped. The window is one copy of at most max-size bytes.
        """
        max_size = max_file_size(max_total_bytes)
        try:
            size = active.stat().st_size
        except FileNotFoundError:
            return
        if size < max_size:
            return
        # Shift the existing rotated files along and drop the oldest, exactly as the writer does.
        rotated_path(active, LOG_FILE_COUNT - 1).unlink(missing_ok=True)
        for index in range(LOG_FILE_COUNT - 2, 0, -1):
            src = rotated_path(active, index)
            if src.exists():
                src.rename(rotated_path(active, index + 1))
        # Carry over only the newest max-size bytes. A burst that outruns the check interval leaves
        # the active file well past max-size, and copying all of it would push a single rotated file
        # over the whole budget — the total is only bounded because every file is. The bytes dropped
        # here are the oldest, which is what the cap says to drop, and the reader serves the tail
        # anyway. Reading a bounded amount also keeps the drop window at one max-size copy rather
        # than chasing a container that is still writing.
        with active.open("rb") as source, rotated_path(active, 1).open("wb") as target:
            remaining = min(size, max_size)
            source.seek(size - remaining)
            while remaining > 0:
                chunk = source.read(min(_LOG_COPY_CHUNK, remaining))
                if not chunk:
                    break
                target.write(chunk)
                remaining -= len(chunk)
        os.truncate(active, 0)

    # ------------------------------------------------------------------ /proc inspection
    @staticmethod
    def _proc_stat_fields(pid: int) -> list[str] | None:
        """``/proc/<pid>/stat`` from the state field on, i.e. field 3 at index 0.

        Split after the LAST ``)``: field 2 is the executable name, unquoted and free to contain
        spaces and parentheses, so a plain split() misaligns every field after it.
        """
        try:
            content = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            return None
        rparen = content.rfind(")")
        if rparen < 0:
            return None
        return content[rparen + 2 :].split()

    def _ppid(self, pid: int) -> int | None:
        fields = self._proc_stat_fields(pid)  # index 0 == field 3 (state); ppid is field 4
        if fields is None:
            return None
        try:
            return int(fields[1])
        except (IndexError, ValueError):
            return None

    def _pid_start_time(self, pid: int) -> int | None:
        """Field 22, the process's start time in clock ticks since boot.

        A PID alone does not identify a process across a restart — the kernel reuses them, and the
        journal would then hand a recovered kernel some unrelated process to signal. The pair
        (pid, start_time) is unique for the life of the boot.
        """
        fields = self._proc_stat_fields(pid)  # field 22 -> index 19
        if fields is None:
            return None
        try:
            return int(fields[19])
        except (IndexError, ValueError):
            return None

    def _alive(self, pid: int) -> bool:
        """Whether the pid is a *live* process. A zombie is not.

        `os.kill(pid, 0)` succeeds for a zombie — the task is dead, only its exit status has yet to
        be reaped — and the pod's supervisor does not reap a dead worker's orphans, so zombies do
        linger here. Counting one as running reports a terminated container as alive to the
        reconciler and lets the journal recover a kernel that is already gone.
        """
        fields = self._proc_stat_fields(pid)  # index 0 == field 3, the state character
        if not fields:
            return False
        return fields[0] not in ("Z", "X", "x")

    def _netns_id(self, pid: int) -> int | None:
        try:
            return Path(f"/proc/{pid}/ns/net").stat().st_ino
        except OSError:
            return None

    def _descendant_pids(self, top_pid: int) -> list[int]:
        children: dict[int, list[int]] = {}
        for entry in os.scandir("/proc"):
            if not entry.name.isdigit():
                continue
            ppid = self._ppid(int(entry.name))
            if ppid is not None:
                children.setdefault(ppid, []).append(int(entry.name))
        out: list[int] = []
        stack = list(children.get(top_pid, []))
        while stack:
            pid = stack.pop()
            out.append(pid)
            stack.extend(children.get(pid, []))
        return out

    async def _find_netns_child(self, proc: asyncio.subprocess.Process) -> int:
        """The descendant sitting in a netns that is not the agent's — the container's stable PID.

        The top launch process stays in the agent's netns (it forks the container into a new one),
        so "the PID we spawned" is the wrong answer and would have the network layer attach the
        veth to the agent's own namespace.
        """
        if self._agent_netns is None:
            self._agent_netns = self._netns_id(os.getpid())
        poll_interval = 0.1
        for _ in range(max(1, int(TASK_START_TIMEOUT_SEC / poll_interval))):
            if proc.returncode is not None:
                raise RuntimeError(
                    f"{self.backend_name} launch exited early (rc={proc.returncode})"
                )
            for pid in self._descendant_pids(proc.pid):
                ns = self._netns_id(pid)
                if ns is not None and ns != self._agent_netns:
                    return pid
            await asyncio.sleep(poll_interval)
        raise TimeoutError(
            f"{self.backend_name} container did not reach its netns'd pause within timeout"
        )

    # ------------------------------------------------------------------ introspection
    @override
    async def list_containers(self) -> Sequence[str]:
        return list(self._pids.keys())

    @override
    async def list_container_infos(self) -> Sequence[ContainerInfo]:
        # In-memory tracking, but it survives an agent restart: open() rebuilds it from the
        # per-container journal (neither runtime has a label store or a container-list API that
        # carries our labels, so the runtime has to keep that map itself). See _record_container.
        infos: list[ContainerInfo] = []
        for cid, pid in self._pids.items():
            infos.append(
                ContainerInfo(
                    id=cid,
                    image=self._images.get(cid, ""),
                    labels=self._labels.get(cid, {}),
                    status="running" if self._alive(pid) else "stopped",
                )
            )
        return infos

    @override
    async def container_pid(self, container_id: str) -> int | None:
        pid = self._pids.get(container_id)
        if pid is None or not self._alive(pid):
            return None
        return pid

    @override
    async def container_status(self, container_id: str) -> str | None:
        pid = self._pids.get(container_id)
        if pid is None:
            return None
        return "running" if self._alive(pid) else "stopped"

    @override
    async def subscribe_task_events(self) -> AsyncIterator[TaskEvent]:
        """Emit an 'exit' the moment a tracked container's process is gone.

        containerd has a daemon event stream; these runtimes have nothing, so this polls. A death
        must be reported EXACTLY ONCE: the agent turns each 'exit' into a CLEAN lifecycle event,
        and the entry stays in ``_pids`` until ``remove_container`` finishes clearing up — several
        seconds later. Re-deriving "is it dead?" from ``_pids`` alone therefore re-fires every tick
        for the whole teardown (measured: 4 CLEAN events in 4 seconds), and the duplicates race the
        first one, so the kernel's recorded reason came out as `already-terminated` instead of
        `self-terminated`. Hence the explicit `reported` set, pruned only when the container leaves
        ``_pids`` for good.
        """
        reported: set[str] = set()
        while True:
            await asyncio.sleep(TASK_POLL_INTERVAL_SEC)
            for cid, pid in list(self._pids.items()):
                if cid in reported or self._alive(pid):
                    continue
                reported.add(cid)
                yield TaskEvent(kind="exit", container_id=cid, exit_code=self._exit_code_of(cid))
            # remove_container has finished with these; drop them so the set cannot grow forever.
            reported &= set(self._pids)

    def _exit_code_of(self, container_id: str) -> int:
        """The container's exit status, or -1 when it cannot be known.

        The launch process propagates the command's status, so its return code is the container's —
        but only for a container this process spawned, and only once it has been reaped. A
        container recovered from the journal after an agent restart is not our child at all, so
        there is no status to collect and the honest answer is "unknown" rather than a fabricated 0
        that would report a crash as a clean exit.
        """
        proc = self._procs.get(container_id)
        if proc is None or proc.returncode is None:
            return -1
        return proc.returncode

    @override
    async def exec_in_container(
        self,
        container_id: str,
        args: Sequence[str],
        *,
        uid: int | None = None,
        gid: int | None = None,
        cwd: str | None = None,
        timeout_sec: float = 30.0,
    ) -> ExecResult:
        # No daemon exec; enter the container process's mount+pid+user namespaces via nsenter.
        # (Only caller today is sudoers provisioning + the file APIs' container-side view.)
        pid = self._pids.get(container_id)
        if pid is None:
            raise RuntimeError(f"no live task for {container_id}")
        nsenter = ["nsenter", "-t", str(pid), "-m", "-p", "-U", "--preserve-credentials"]
        if cwd is not None:
            nsenter += ["--wd", cwd]
        rc, out, err = await self._run(*nsenter, "--", *args)
        return ExecResult(exit_code=rc, stdout=out, stderr=err)
