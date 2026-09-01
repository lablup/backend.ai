"""``SelfHostedRootlessRuntime`` — the agent itself holding a container that has no monitor.

enroot and apptainer exec the container in place: there is no daemon, no shim, no conmon. The
kernel process is a child of the agent, and nothing else knows it exists. So everything containerd
gets from its daemon has to be done here — journal the PID so an agent restart can find the
container again, hold the process and reap it, create the cgroup (through the privnet when the
agent is unprivileged), open and rotate the log, and emulate a start gate.

That last one is the load-bearing piece. The agent's attach sequence is

    handle = await runtime.create_task(cid)   # netns exists, user command NOT exec'd
    await network.attach(..., task_pid=handle.pid)
    await runtime.start_task(cid)             # release the gate -> exec

which neither runtime has natively -- both exec immediately. It is emulated with a small wrapper
that enters the namespaces, signals readiness, blocks on a FIFO, then ``exec``s the real command,
preserving the PID the network layer attached to. That is the entire runtime-specific contract for
BEP-1062: *produce an attachable netns and a stable PID*.

A backend subclasses this and supplies only what genuinely differs:

* ``_runtime_env`` -- the runtime's own configuration environment (``ENROOT_*`` / ``APPTAINER_*``).
* ``_launch_argv`` -- the command line that starts one container, running the pause wrapper.
* ``_discard_container`` -- dropping the runtime's own record of a container, on removal.
* the image surface (``pull_image`` / ``commit_container`` / ``push_image`` / ...), which is where
  a squashfs archive and a sandbox directory genuinely part ways.

None of that machinery is owed to the agent as such -- see
:mod:`ai.backend.agent.rootless.runtime` for what is, and why a rootless runtime that brings its
own monitor sits beside this class rather than under it.
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
from abc import abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path
from typing import IO, Any, Final, cast, override

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
    TaskEvent,
    TaskHandle,
)
from ai.backend.agent.containerd.runtime.spec import container_cgroup_fs_path
from ai.backend.agent.network.journal_io import atomic_write
from ai.backend.agent.rootless.gate import GATE_MNT, signal_go, wait_ready, write_gate
from ai.backend.agent.rootless.runtime import RootlessOciRuntime
from ai.backend.agent.rootless.seccomp import compile_profile
from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

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
exec {_KRUNNER_PYTHON} {GATE_MNT}/{SECCOMP_INSTALLER} - "$@"
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
# How much of the container log a failed launch carries into its exception.
_LAUNCH_DIAGNOSIS_LINES: Final = 15
# Neither runtime has an event stream, so container death is polled for.
TASK_POLL_INTERVAL_SEC: Final = 1.0
# How often each live container's log is measured against the cap. A stat() per container is
# nothing, and the interval is what bounds the overshoot (see _rotate_logs_loop).
LOG_ROTATE_INTERVAL_SEC: Final = 5.0
_LOG_COPY_CHUNK: Final = 1024 * 1024


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


class SelfHostedRootlessRuntime(RootlessOciRuntime):
    """The agent holds the container itself. See the module docstring."""

    # container_id -> the OCI spec handed to create_task (re-read on start/limits).
    _specs: dict[str, Mapping[str, Any]]
    # container_id -> the user command, split out of the spec at create time.
    _commands: dict[str, list[str]]
    # container_id -> the PID the network layer attaches to (the pause wrapper, then the exec'd
    # command: the wrapper execs in place, so the PID never moves).
    _pids: dict[str, int]
    # container_id -> the top launch subprocess (owns the process tree; awaited on exit).
    _procs: dict[str, asyncio.subprocess.Process]
    # container_id -> source image ref, so remove/commit can find the image.
    _images: dict[str, str]
    _log_root: Path | None
    # container_logs.max_length: the total budget across the active log and its rotated siblings.
    # 0 until configure_logging() runs (which is after open()), meaning "not configured, do not
    # rotate" rather than "rotate at zero bytes".
    _log_max_bytes: int
    # The periodic in-place rotation task; see _rotate_logs_loop.
    _rotator_task: asyncio.Task[None] | None
    # This agent's own netns inode, to tell the container's dedicated netns apart from ours.
    _agent_netns: int | None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._specs = {}
        self._commands = {}
        self._pids = {}
        self._procs = {}
        self._images = {}
        self._log_root = None
        self._log_max_bytes = 0
        self._rotator_task = None
        self._agent_netns = None

    # ------------------------------------------------------------------ backend hooks
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
                env={**self._process_env(), **self._launch_env(spec)},
                # `setsid` in the child: its own session and process group, no controlling
                # terminal. These runtimes have no daemon, so the kernel is a CHILD of the agent —
                # and everything about recovery here (the journal, `_recover_containers`,
                # `container_pid` falling back to it) is built on the kernel outliving the agent.
                # Without this it does not: a signal aimed at the agent's process group takes the
                # kernel with it, which is what an operator's Ctrl+C, a closing terminal, and tmux
                # killing its session all send. Measured: restarting the agent that way killed a
                # running session's kernel outright, leaving the manager holding a RUNNING session
                # with nothing behind it. Reaping is unaffected — `_reap` and `_signal` address the
                # pid, never the group.
                #
                # This is not the whole story, and it is worth being exact about what it does NOT
                # cover. systemd's default KillMode=control-group signals a unit's *cgroup*, which
                # a new session does not leave. What keeps a kernel out of that blast is the
                # separate top-level cgroup the privnet makes for it
                # (`/sys/fs/cgroup/backend-ai/<kernel-id>`, see `_confine_via_privnet`) — measured:
                # the kernel is not among the pids in the agent's own cgroup. That delegation is
                # best-effort, so on a node where it fails the kernel stays in the agent's cgroup
                # and an `systemctl stop` does take it. Nor does any of this survive the agent's
                # whole container or pod being torn down, where the boundary is the pod's.
                start_new_session=True,
            )
        finally:
            os.close(log_fd)
        self._procs[container_id] = proc
        try:
            await self._wait_ready(proc, gate_dir, container_id)
            pid = await self._find_netns_child(proc)
        except BaseException:
            await self._reap(container_id)
            raise
        self._pids[container_id] = pid
        await asyncio.to_thread(self._record_container, container_id, pid)
        try:
            await self._set_hostname(pid, spec.get("hostname"))
            # Confine the container now, while the wrapper is still blocked on the gate: every
            # process that will run the user's command is already forked, and none of it has
            # started. Doing it after start_task would let the workload run unconfined for however
            # long the move takes — and it is also what makes failing here safe, because there is
            # no workload to have observed the unconfined window.
            if self._privnet_socket is not None:
                await self._confine_via_privnet(container_id, spec, proc.pid)
            else:
                await asyncio.to_thread(self._confine, container_id, spec, proc.pid)
        except BaseException:
            await self._abandon_container(container_id)
            raise
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
        if self._privnet_socket is not None:
            # Whoever created the cgroup has to be the one to remove it: an unprivileged agent
            # cannot rmdir under /sys/fs/cgroup any more than it could mkdir there.
            await self._release_via_privnet(container_id)
        else:
            await asyncio.to_thread(self._remove_cgroup, container_id)
        self._specs.pop(container_id, None)
        self._commands.pop(container_id, None)
        self._pids.pop(container_id, None)
        self._images.pop(container_id, None)
        self._labels.pop(container_id, None)

    async def _abandon_container(self, container_id: str) -> None:
        """Undo a container that was created but is not going to become one.

        The reap on the earlier failure path is enough while the container is only a process. Past
        the point where it is journalled and in `_pids` it is not: a journal entry left behind is
        adopted by the next recovery as a *running* container — holding its slots, and safe from
        the orphan sweep for as long as its PID happens to be reused — and its log is one that
        nothing else ever removes, because `remove_container` is the only thing that unlinks a log
        and this container will never reach it.

        So it takes down the same set `remove_container` does, minus the runtime's own discard: the
        container never started, so there is nothing for the runtime to discard.
        """
        await self._reap(container_id)
        self._pids.pop(container_id, None)
        await asyncio.to_thread(unlink_log_files, self._log_path(container_id))
        await asyncio.to_thread(force_rmtree, self._state_path / container_id)

    async def _reap(self, container_id: str) -> None:
        proc = self._procs.pop(container_id, None)
        if proc is not None and proc.returncode is None:
            proc.kill()
            await proc.wait()

    # ------------------------------------------------------------------ the two-phase gate
    def _gate_dir(self, container_id: str) -> Path:
        return self._state_path / container_id / "gate"

    def _write_gate(self, gate_dir: Path) -> None:
        write_gate(gate_dir, PAUSE_SCRIPT, uid=self._kernel_uid, gid=self._kernel_gid)

    def _write_seccomp(self, gate_dir: Path, spec: Mapping[str, Any]) -> None:
        """Compile this container's seccomp profile into the gate, for the pause wrapper to apply.

        Absent profile means the operator chose the jail sandbox (the agent then does not generate
        one) — that is a deliberate posture, not a failure, so there is simply no filter to install.
        A profile that is present but will not compile IS a failure: starting the container anyway
        would silently run it unconfined.
        """
        # The helper runs on EVERY launch, filter or not: it also unshares the IPC namespace, which
        # neither runtime does for us. So it is always staged; only the filter is conditional.
        shutil.copyfile(_SECCOMP_INSTALLER_SRC, gate_dir / SECCOMP_INSTALLER)
        oci_seccomp = spec.get("seccomp")
        if not oci_seccomp:
            return
        program = compile_profile(oci_seccomp, arch=CURRENT_ARCH)
        (gate_dir / SECCOMP_FILTER).write_bytes(program)
        log.debug(
            "[{}] seccomp: {} instructions for {}",
            self.backend_name,
            len(program) // 8,
            CURRENT_ARCH,
        )

    def _launch_diagnosis(self, container_id: str) -> str:
        """The tail of what the runtime printed while failing to reach the pause.

        The launch writes stdout/stderr into the container log rather than a pipe (the log has to
        survive an agent restart), so a bare returncode is all the caller would otherwise see —
        and `rc=1` says nothing about whether the image, the userns, or a missing file capability
        was the problem. Best-effort: a diagnosis must never mask the failure it describes.
        """
        try:
            text = self._log_path(container_id).read_text(errors="replace")
        except OSError:
            return ""
        tail = [line for line in text.splitlines() if line.strip()][-_LAUNCH_DIAGNOSIS_LINES:]
        return ("\n" + "\n".join(tail)) if tail else ""

    async def _wait_ready(
        self, proc: asyncio.subprocess.Process, gate_dir: Path, container_id: str
    ) -> None:
        try:
            async with asyncio.timeout(TASK_START_TIMEOUT_SEC):
                await wait_ready(
                    gate_dir,
                    failure=lambda: (
                        None
                        if proc.returncode is None
                        else (
                            f"{self.backend_name} launch exited before pause "
                            f"(rc={proc.returncode}):{self._launch_diagnosis(container_id)}"
                        )
                    ),
                )
        except TimeoutError:
            raise TimeoutError(
                f"{self.backend_name} container did not reach the pause (no ready marker):"
                f"{self._launch_diagnosis(container_id)}"
            ) from None

    def _signal_go(self, go_fifo: Path) -> None:
        signal_go(go_fifo.parent)

    def _log_hardening_disposition(self, container_id: str, spec: Mapping[str, Any]) -> None:
        # Make the hardening model explicit and observable. Capabilities are dropped by design
        # (the userns scopes them), and no MAC profile is applied — the same as every other backend
        # here. Syscall filtering comes from the compiled seccomp filter above, or — when the
        # operator picked the jail sandbox and so no profile was generated — from jail alone.
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

    def _adopt_journal_entry(self, container_id: str, *, drop_stale: bool = True) -> bool:
        """Load one journalled container into the in-memory tables. True when it is live.

        Split out of ``_recover_containers`` because the journal — not this process's memory — is
        what makes the runtime readable by a SECOND process. The privnet daemon holds its own
        runtime client and is asked about containers this instance never created, so a miss has to
        fall back to the journal rather than answer "no such container".
        """
        entry = self._state_path / container_id
        try:
            meta = json.loads((entry / "container.json").read_text())
        except FileNotFoundError:
            return False
        except (OSError, ValueError) as e:
            log.warning("[{}] unreadable container journal {}: {!r}", self.backend_name, entry, e)
            return False
        pid = meta.get("pid")
        if not isinstance(pid, int):
            return False
        # The PID must still be the same *live* process: not exited, not a zombie, and not a
        # reused number (which is what the start time rules out).
        if not self._alive(pid) or self._pid_start_time(pid) != meta.get("start_time"):
            log.debug("[{}] journal entry {} is stale; dropping", self.backend_name, container_id)
            if drop_stale:
                shutil.rmtree(entry, ignore_errors=True)
            self._pids.pop(container_id, None)
            self._images.pop(container_id, None)
            self._labels.pop(container_id, None)
            return False
        self._pids[container_id] = pid
        self._images[container_id] = str(meta.get("image") or "")
        self._labels[container_id] = dict(meta.get("labels") or {})
        return True

    def _rescan_journal(self) -> None:
        """Re-read every journalled container. Cheap (one small read per container) and what lets
        a second process see containers created after it started."""
        if not self._state_path.is_dir():
            return
        for entry in self._state_path.iterdir():
            self._adopt_journal_entry(entry.name)

    def _recover_containers(self) -> None:
        """Rebuild the in-memory container tables from the journal, dropping what is no longer live."""
        self._rescan_journal()
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
            return  # cgroup v1 host: a standing property of the node, not a failed attempt
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
        await asyncio.to_thread(self._rescan_journal)
        infos: list[ContainerInfo] = []
        for cid, pid in list(self._pids.items()):
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
        if pid is None:
            # Not ours *yet*: another process (the agent) may have created it since this instance
            # opened. The journal is the shared record, so consult it before denying the container.
            if not await asyncio.to_thread(self._adopt_journal_entry, container_id):
                return None
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
