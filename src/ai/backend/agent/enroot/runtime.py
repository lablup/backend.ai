"""``EnrootRuntime`` — an :class:`~ai.backend.agent.containerd.runtime.interface.OciRuntime`
implementation backed by the **enroot** CLI (squashfs images + userns), replacing the
containerd gRPC daemon.

The containerd agent builds a full OCI runtime spec and hands it to the runtime; this class
translates that spec to enroot invocations. Key differences from the containerd runtime:

* **Images** are ``.sqsh`` squashfs files under ``data_path``. There is no registry client or
  content store, so ``pull_image`` shells out to ``enroot import docker://<ref>`` and a JSON
  **sidecar** (``<slug>.json``) records the identity the OCI model needs — config digest and the
  kernel-spec / base-distro labels — because a ``.sqsh`` cannot be queried for OCI config.
* **The two-phase task model** (``create_task`` returns a PID in the 'created' state *before*
  the user command execs, the network layer attaches CNI to ``/proc/<pid>/ns/net``, then
  ``start_task`` resumes it) has no native enroot equivalent — ``enroot start`` execs
  immediately. It is emulated with a small **pause-wrapper** entrypoint that sets up the
  namespaces, signals readiness (so the PID is attachable), waits on a FIFO, then execs the real
  command. See ``create_task`` / ``start_task``.
* **Hardening**: the **capability** set and **AppArmor** profile are dropped — the userns already
  scopes caps to the pod, and enroot has no AppArmor integration. OCI **seccomp** is a runc feature
  (runc compiles the profile to BPF); enroot has no runc and the agent has no libseccomp to
  precompile one, so syscall filtering is delegated to BAI's runtime-independent **jail** sandbox
  (``sandbox_type=jail``), which the krunner entrypoint installs in-container regardless of runtime.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import shutil
import time
from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Final, override

from ai.backend.agent.containerd.log_writer import (
    LOG_FILE_COUNT,
    max_file_size,
    rotated_path,
)
from ai.backend.agent.containerd.logs import unlink_log_files
from ai.backend.agent.containerd.runtime.interface import (
    ContainerInfo,
    ExecResult,
    ImageInfo,
    OciRuntime,
    TaskEvent,
    TaskHandle,
)
from ai.backend.agent.containerd.runtime.spec import container_cgroup_fs_path
from ai.backend.agent.enroot.registry import fetch_image_metadata
from ai.backend.agent.network.journal_io import atomic_write
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

_ENROOT_BIN: Final = "enroot"
# enroot slugifies a docker ref into a squashfs filename; we keep the ref in the sidecar and use a
# filesystem-safe slug for the on-disk names so a ref round-trips via the sidecar, not the name.
_SLUG_RE: Final = re.compile(r"[^A-Za-z0-9_.-]+")

# The per-container gate directory (pause script + go FIFO) is bind-mounted here inside the
# container; a top-level hidden path avoids colliding with the image / OCI-spec mounts.
_GATE_MNT: Final = "/.bai-enroot-gate"
# The two-phase pause: enroot runs this as the container command. It (1) writes a `ready` marker so
# create_task knows the wrapper — not a transient enroot setup process — is the stable netns holder,
# then (2) blocks in the shell itself (`read`, no child `cat`) opening the go FIFO, so this exact PID
# is what create_task attaches to; on go it `exec`s the real command, preserving that PID.
_PAUSE_SCRIPT: Final = (
    f'#!/bin/sh\n: > {_GATE_MNT}/ready\nread _ < {_GATE_MNT}/go 2>/dev/null\nexec "$@"\n'
)
# OCI mount types that enroot provides itself (userns) — never forwarded as host binds.
_SKIP_MOUNT_TYPES: Final = frozenset({
    "proc",
    "sysfs",
    "tmpfs",
    "cgroup",
    "cgroup2",
    "mqueue",
    "devpts",
    "devtmpfs",
})
# How long create_task waits for the enroot container to reach its netns'd pause.
_TASK_START_TIMEOUT_SEC: Final = 30.0
# How often each live container's log is measured against the cap. A stat() per container is
# nothing, and the interval is what bounds the overshoot (see _rotate_logs_loop), so keep it short.
_LOG_ROTATE_INTERVAL_SEC: Final = 5.0
_LOG_COPY_CHUNK: Final = 1024 * 1024
# Presence of the unified hierarchy's controller list is what tells cgroup v2 from v1.
_CGROUP_V2_MARKER: Final = "/sys/fs/cgroup/cgroup.controllers"
# rmdir on a cgroup whose members are still exiting returns EBUSY; ~1s total is far more than the
# kernel needs to reap processes that have already been SIGKILLed.
_CGROUP_RMDIR_RETRIES: Final = 20
_CGROUP_RMDIR_DELAY_SEC: Final = 0.05
# Docker's default ShmSize, used when the session did not ask for one.
_DEFAULT_SHM_BYTES: Final = 64 * 1024 * 1024


def _slug(image_ref: str) -> str:
    return _SLUG_RE.sub("+", image_ref)


class EnrootRuntime(OciRuntime):
    _data_path: Path
    _cache_path: Path
    _runtime_path: Path
    # Gate dirs (pause script + go FIFO) and container logs. MUST live outside the ENROOT_* paths:
    # enroot hides ENROOT_RUNTIME_PATH inside the container's mount ns, so a bind source under it is
    # invisible to enroot-mount ("No such file or directory").
    _state_path: Path
    # oci_spec handed in at create_container, kept until the task is built (enroot consumes it as
    # mounts/env/hooks, not as a spec file).
    _specs: dict[str, Mapping[str, Any]]
    # container_id -> the real command (kernel entrypoint + args) to exec after the gate opens.
    _commands: dict[str, Sequence[str]]
    # container_id -> netns-holder host PID (the enroot command process), for netns attach + kill.
    _pids: dict[str, int]
    # container_id -> the top `enroot start` subprocess (owns the process tree; awaited on exit).
    _procs: dict[str, asyncio.subprocess.Process]
    # container_id -> source image ref, so remove/commit can find the .sqsh.
    _images: dict[str, str]
    # container_id -> the OCI spec's labels (KERNEL_ID_LABEL/OWNER_AGENT_LABEL/...). enumerate_
    # containers filters on these to reconcile live kernels + rebuild the resource alloc map, so an
    # empty set here would drop every enroot container from reconstruct_resource_usage.
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

    # ------------------------------------------------------------------ lifecycle
    @override
    async def open(self) -> None:
        # enroot runs as the kernel uid (rootless; see _enroot_credentials), so its data/cache/runtime
        # and the per-container state (gate/logs) live must be owned by that uid, not root. Hand over
        # the roots; per-container children inherit via the kernel-uid-run enroot / _write_gate. No-op
        # when the agent already runs as the kernel uid.
        own = os.geteuid() != self._kernel_uid
        for p in (self._data_path, self._cache_path, self._runtime_path, self._state_path):
            p.mkdir(parents=True, exist_ok=True)
            if own:
                os.chown(p, self._kernel_uid, self._kernel_gid)
        await asyncio.to_thread(self._recover_containers)
        if self._rotator_task is None:
            self._rotator_task = asyncio.create_task(self._rotate_logs_loop())

    @override
    async def close(self) -> None:
        if self._rotator_task is not None:
            self._rotator_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._rotator_task
            self._rotator_task = None

    def _env(self) -> dict[str, str]:
        return {
            "ENROOT_DATA_PATH": str(self._data_path),
            "ENROOT_CACHE_PATH": str(self._cache_path),
            "ENROOT_RUNTIME_PATH": str(self._runtime_path),
            # BAI clusters commonly run an internal plain-HTTP registry; enroot import defaults to
            # https and would fail the TLS handshake against it. (A dedicated config knob can gate
            # this per-registry later.)
            "ENROOT_ALLOW_HTTP": "y",
        }

    def _process_env(self) -> dict[str, str]:
        # The environment enroot itself is launched with. enroot's `98-nvidia` hook prefers a
        # NVIDIA_* variable already present in its own environment over the container's env file
        # (`[ -v "${key}" ] || export ...`), so anything the agent's pod inherited — a GPU-enabled
        # fatPod sets NVIDIA_VISIBLE_DEVICES=all to get the driver injected into *itself* — would
        # otherwise override the per-kernel allocation and hand every device to every container.
        # Strip NVIDIA_* here so the container env file (built from the OCI spec) is authoritative.
        inherited = {k: v for k, v in os.environ.items() if not k.startswith("NVIDIA_")}
        return {**inherited, **self._env()}

    async def _run(
        self, *argv: str, extra_env: Mapping[str, str] | None = None
    ) -> tuple[int, bytes, bytes]:
        env = {**self._process_env(), **(extra_env or {})}
        proc = await asyncio.create_subprocess_exec(
            *self._enroot_prefix(),
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode or 0, stdout, stderr

    def _enroot_prefix(self) -> list[str]:
        # Run enroot **as the kernel uid**, not as the (root) agent — as an argv prefix (`setpriv`)
        # rather than the subprocess user=/group= kwargs, which uvloop (this agent's event loop) does
        # not accept. Dropping to a non-root uid is what makes enroot install a rootless user namespace:
        # with `--root` it then maps container-root -> this uid (uid_map "0 <kernel_uid> 1"), so the
        # container's root IS the kernel uid on the host. The scratch dirs are chowned to the kernel
        # uid, so container-root owns them and /tmp (enroot's 755 root-owned tmpfs is now root ==
        # kernel_uid) — everything aligns with no host privilege and no identity-map/`chmod` workaround.
        # No-op when the agent already runs as the kernel uid (a non-privileged deployment). Requires
        # the host prerequisites the krunner entrypoint sets up: /etc/sub{u,g}id for the uid and file
        # caps on newuidmap/newgidmap.
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

    # ------------------------------------------------------------------ images
    def _sqsh(self, image_ref: str) -> Path:
        return self._data_path / f"{_slug(image_ref)}.sqsh"

    def _meta(self, image_ref: str) -> Path:
        return self._data_path / f"{_slug(image_ref)}.json"

    def _read_meta(self, image_ref: str) -> dict[str, Any] | None:
        p = self._meta(image_ref)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    @override
    async def image_exists(self, image_ref: str) -> bool:
        return self._sqsh(image_ref).exists()

    @override
    async def image_digest(self, image_ref: str) -> str | None:
        meta = self._read_meta(image_ref)
        return meta.get("digest") if meta else None

    @override
    async def image_config_digest(self, image_ref: str) -> str | None:
        meta = self._read_meta(image_ref)
        return meta.get("config_digest") if meta else None

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        # `enroot import` produces the .sqsh. Registry auth flows through ENROOT_* credentials
        # (or ~/.docker/config.json); wire `auth` into an ENROOT credential file in a later pass.
        sqsh = self._sqsh(image_ref)
        rc, _out, err = await self._run(
            _ENROOT_BIN, "import", "-o", str(sqsh), f"docker://{image_ref}"
        )
        if rc != 0:
            raise RuntimeError(
                f"enroot import failed for {image_ref}: {err.decode(errors='replace')}"
            )
        # A `.sqsh` cannot be queried for OCI config, so record the identity scan_images/check_image
        # need — config-blob digest (Docker's `Id`, the manager's image_id) + kernel-spec/base-distro
        # labels + architecture + entrypoint — from the registry. A failed probe leaves them null
        # (check_image then re-pulls, never blocks).
        meta = await fetch_image_metadata(image_ref, auth)
        self._meta(image_ref).write_text(
            json.dumps({
                "ref": image_ref,
                "digest": meta.config_digest if meta else None,
                "config_digest": meta.config_digest if meta else None,
                "architecture": meta.architecture if meta else "",
                "labels": dict(meta.labels) if meta else {},
                "entrypoint": meta.entrypoint if meta else None,
            })
        )

    @override
    async def list_images(self) -> Sequence[str]:
        refs: list[str] = []
        for meta_file in self._data_path.glob("*.json"):
            try:
                refs.append(json.loads(meta_file.read_text())["ref"])
            except (OSError, ValueError, KeyError):
                continue
        return refs

    @override
    async def list_image_infos(self) -> Sequence[ImageInfo]:
        infos: list[ImageInfo] = []
        for ref in await self.list_images():
            meta = self._read_meta(ref) or {}
            infos.append(
                ImageInfo(
                    name=ref,
                    digest=meta.get("config_digest") or "",
                    architecture=meta.get("architecture") or "",
                    labels=meta.get("labels") or {},
                )
            )
        return infos

    @override
    async def remove_image(self, image_ref: str, *, sync: bool = False) -> None:
        self._sqsh(image_ref).unlink(missing_ok=True)
        self._meta(image_ref).unlink(missing_ok=True)

    @override
    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        # enroot has no push. The commit/customized-image flow would need `enroot export` + a
        # separate skopeo/oras upload; unsupported in the first pass.
        raise NotImplementedError("enroot backend does not support push_image")

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        # The downloadable artifact is the squashfs itself for enroot.
        sqsh = self._sqsh(image_ref)
        if not sqsh.exists():
            raise FileNotFoundError(f"no local .sqsh for {image_ref}")
        await asyncio.to_thread(shutil.copyfile, sqsh, dest_path)

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        meta = self._read_meta(image_ref)
        return meta.get("entrypoint") if meta else None

    # ------------------------------------------------------------------ container lifecycle
    @override
    async def create_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: Mapping[str, Any],
        network: str = "none",
    ) -> None:
        # enroot has no "create then start" split at this layer; retain the OCI spec (mounts/env/
        # entrypoint) and materialize the container rootfs now. The real command is deferred to
        # start_task (run behind the two-phase gate).
        self._specs[container_id] = oci_spec
        self._commands[container_id] = list(command)
        self._images[container_id] = image_ref
        self._labels[container_id] = dict(oci_spec.get("labels") or {})
        self._log_hardening_disposition(container_id, oci_spec)
        rc, _out, err = await self._run(
            _ENROOT_BIN, "create", "--force", "--name", container_id, str(self._sqsh(image_ref))
        )
        if rc != 0:
            raise RuntimeError(
                f"enroot create failed for {container_id}: {err.decode(errors='replace')}"
            )

    @override
    def configure_logging(self, launcher: Path, log_root: Path, max_total_bytes: int) -> None:
        # enroot has no log driver at all — no config knob, no CLI flag, nothing in its runtime
        # library: `enroot start` execs the command with the invoker's stdio inherited (upstream's
        # model is that the caller — Slurm, in enroot's usual pairing — owns redirection). So the
        # `launcher` (containerd's binary:// writer, which containerd itself starts and which owns
        # the write end) has nobody to start it here; the container writes straight to our file
        # descriptor instead, and the size cap has to be enforced from the outside. See
        # _rotate_logs_loop.
        self._log_root = log_root
        self._log_max_bytes = max_total_bytes

    @override
    async def create_task(self, container_id: str, *, use_logger: bool = True) -> TaskHandle:
        # Two-phase emulation (see module docstring). Launch `enroot start` with a dedicated netns
        # (--net) + PID ns (--pid), running the pause-wrapper as the command: the container comes
        # up, enters its own netns, and BLOCKS before exec'ing the real command. Its host PID (the
        # netns holder — verified to be the command process, a descendant of the top enroot proc)
        # is returned so the network layer can attach veth to /proc/<pid>/ns/net; start_task then
        # opens the go FIFO to resume it. The wrapper's `exec` preserves this PID across the resume.
        spec = self._specs[container_id]
        gate_dir = self._gate_dir(container_id)
        await asyncio.to_thread(self._write_gate, gate_dir)
        argv = self._enroot_start_argv(container_id, spec, gate_dir)
        log.debug("[enroot] start argv: {}", " ".join(argv))
        log_fd = self._open_log(container_id)
        try:
            proc = await asyncio.create_subprocess_exec(
                *self._enroot_prefix(),
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

    def _log_hardening_disposition(self, container_id: str, spec: Mapping[str, Any]) -> None:
        # Make the enroot hardening model explicit and observable. Capabilities and AppArmor are
        # dropped by design (userns scopes caps; enroot has no AppArmor). OCI seccomp is a runc
        # feature — enroot cannot apply it (no runc; the agent has no libseccomp to precompile a
        # BPF), so syscall filtering must come from BAI's runtime-independent `jail` sandbox
        # (sandbox_type=jail), which the krunner entrypoint installs in-container regardless of the
        # runtime. Warn once per container when a profile is present but no jail is in effect.
        linux = spec.get("linux", {})
        if "seccomp" in linux:
            log.warning(
                "[enroot] OCI seccomp profile present but not enforceable by enroot (no runc); "
                "use sandbox_type=jail for syscall filtering (container {})",
                container_id,
            )

    # --- two-phase gate + netns-holder discovery helpers ---
    def _gate_dir(self, container_id: str) -> Path:
        return self._state_path / container_id / "gate"

    def _write_gate(self, gate_dir: Path) -> None:
        gate_dir.mkdir(parents=True, exist_ok=True)
        script = gate_dir / "pause.sh"
        script.write_text(_PAUSE_SCRIPT)
        script.chmod(0o755)
        fifo = gate_dir / "go"
        if not fifo.exists():
            os.mkfifo(fifo, 0o600)
        # The container runs as the kernel uid (see _enroot_credentials), so it — not the root agent —
        # is what writes the `ready` marker into the gate dir and reads the `go` FIFO. Hand the gate
        # (and its parent, the per-container state dir) to the kernel uid so those cross into the
        # container. No-op when the agent already runs as the kernel uid.
        if os.geteuid() != self._kernel_uid:
            os.chown(gate_dir.parent, self._kernel_uid, self._kernel_gid)
            os.chown(gate_dir, self._kernel_uid, self._kernel_gid)
            os.chown(script, self._kernel_uid, self._kernel_gid)
            os.chown(fifo, self._kernel_uid, self._kernel_gid)

    async def _wait_ready(self, proc: asyncio.subprocess.Process, gate_dir: Path) -> None:
        # Wait until the pause-wrapper writes its `ready` marker (it has reached the FIFO pause and
        # is the stable netns holder) before attaching — avoids racing a transient enroot setup PID.
        ready = gate_dir / "ready"
        poll = 0.1
        for _ in range(max(1, int(_TASK_START_TIMEOUT_SEC / poll))):
            if ready.exists():
                return
            if proc.returncode is not None:
                raise RuntimeError(f"enroot start exited before pause (rc={proc.returncode})")
            await asyncio.sleep(poll)
        raise TimeoutError("enroot container did not reach the pause (no ready marker)")

    def _signal_go(self, go_fifo: Path) -> None:
        with go_fifo.open("w") as f:
            f.write("go\n")

    def _log_path(self, container_id: str) -> Path:
        # The path the agent's reader expects (containerd.runtime.grpc.container_log_path); it must
        # stay in step with it, so the log root is whatever configure_logging was handed.
        if self._log_root is not None:
            return self._log_root / f"{container_id}.log"
        return self._state_path / container_id / "container.log"

    def _open_log(self, container_id: str) -> int:
        # enroot has no binary:// log launcher; capture the container's stdio to a file the agent
        # can tail (get_logs). Returns an fd handed to the subprocess; the caller closes its copy.
        # O_APPEND is what makes the out-of-band rotation in _rotate_log() safe.
        path = self._log_path(container_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

    async def _set_hostname(self, pid: int, hostname: str | None) -> None:
        """Give the container its cluster hostname (`main1`, `sub1`, ...).

        runc applies the OCI spec's hostname; enroot has no equivalent and a fresh UTS namespace
        just inherits the agent's, so without this every kernel calls itself by the agent pod's
        name — wrong for anything that treats the hostname as its cluster identity (MPI, some
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
                "[enroot] could not set the hostname of pid {} to {}: {}",
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

        enroot has no daemon and no label store: `enroot list` knows names, not our kernel labels,
        and nothing on the host maps a container to its netns-holder PID. Without this the runtime's
        knowledge of running containers is process memory, and an agent worker restart — which the
        containers *survive*, being reparented to the pod's supervisor — leaves the fresh runtime
        reporting none of them. reconstruct_resource_usage would then free every slot and the
        orphan-kernel sweep could kill live kernels.
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
                log.warning("[enroot] unreadable container journal {}: {!r}", path, e)
                continue
            pid = meta.get("pid")
            if not isinstance(pid, int):
                continue
            # The PID must still be the same *live* process: not exited, not a zombie, and not a
            # reused number (which is what the start time rules out).
            if not self._alive(pid) or self._pid_start_time(pid) != meta.get("start_time"):
                log.debug("[enroot] journal entry {} is stale; dropping", entry.name)
                shutil.rmtree(entry, ignore_errors=True)
                continue
            self._pids[entry.name] = pid
            self._images[entry.name] = str(meta.get("image") or "")
            self._labels[entry.name] = dict(meta.get("labels") or {})
        if self._pids:
            log.info("[enroot] recovered {} running container(s) from the journal", len(self._pids))

    # ------------------------------------------------------------------ cgroup confinement
    def _confine(self, container_id: str, spec: Mapping[str, Any], top_pid: int) -> None:
        """Put the container's whole process tree in its own cgroup, with the allocated limits.

        runc does this from the OCI spec's ``linux.resources`` + ``cgroupsPath``; enroot has no
        cgroup integration at all, so without this the container simply inherits the agent's cgroup
        — meaning a kernel allocated 2 CPUs can saturate the node, and the agent's stats reader
        finds nothing at the path it expects (``/sys/fs/cgroup/backend-ai/<kernel-id>``), so every
        kernel reports no CPU or memory utilization at all. Both are the same missing cgroup.

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
                continue  # a transient enroot setup process that already exited
            except OSError as e:
                log.warning("[enroot] cannot move pid {} into {}: {!r}", pid, cgroup, e)

    def _create_cgroup(self, container_id: str, spec: Mapping[str, Any]) -> Path | None:
        """Create the kernel's cgroup and write its limits. None when this host cannot do it."""
        if not Path(_CGROUP_V2_MARKER).exists():
            # cgroup v1 splits every controller into its own hierarchy; the agent's stats reader
            # composes those per-controller mount points itself. Rather than half-apply limits
            # across trees, say plainly that this host gets none.
            log.warning(
                "[enroot] cgroup v1 host: per-kernel CPU/memory limits and stats are NOT applied"
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
            log.warning("[enroot] cannot create the cgroup {}: {!r}", cgroup, e)
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
                log.warning("[enroot] cannot set {}={} on {}: {!r}", name, value, cgroup, e)

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
        log.warning("[enroot] could not reclaim the cgroup {}; it will be left behind", cgroup)

    # ------------------------------------------------------------------ log rotation
    async def _rotate_logs_loop(self) -> None:
        """Cap each live container's log the way the containerd log writer does.

        containerd gets a hard cap for free: it starts our `binary://` writer, which owns the write
        end and simply opens a new file when the active one is full. enroot has no equivalent — the
        container holds our file descriptor for its whole life — so the cap has to be applied from
        outside, by watching the file and rotating it underneath the writer.

        That makes the cap a *soft* one: the log can overshoot by whatever the container writes
        between two checks. The alternative — handing the container a pipe and reading it here —
        buys a hard cap at the price of blocking the container's stdout whenever the reader is gone,
        and kernels are meant to outlive an agent restart. An overshooting log file is recoverable;
        a kernel wedged on a full pipe is not.
        """
        while True:
            await asyncio.sleep(_LOG_ROTATE_INTERVAL_SEC)
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
                log.warning("[enroot] cannot list the container log root: {!r}", e)
                continue
            for active in actives:
                try:
                    await asyncio.to_thread(self._rotate_log, active, self._log_max_bytes)
                except Exception:
                    log.exception("[enroot] rotating {} failed", active)

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

    def _enroot_start_argv(
        self, container_id: str, spec: Mapping[str, Any], gate_dir: Path
    ) -> list[str]:
        # enroot -m FSTAB: `x-create=auto` makes enroot create the mountpoint (file or dir, matching
        # the source) inside the container — the OCI spec's targets do not pre-exist in the image
        # rootfs. `bind` + `ro`/`rw` set the mode.
        argv = [
            _ENROOT_BIN,
            "start",
            # --root remaps container-root to the (kernel-uid) invoker. Combined with running enroot
            # as the kernel uid (see _enroot_credentials), the container's root IS the kernel uid on
            # the host, which owns the scratch — so the kernel-runner, staying root inside, reads its
            # ssh host key / jupyter config and writes /tmp with no remap tricks and no host privilege.
            "--root",
            "--net",
            "--pid",
            # A private UTS namespace, so the kernel can carry its own cluster hostname instead of
            # the agent's. enroot does not *set* one — a fresh UTS ns inherits the parent's — so
            # create_task assigns it once the container is up.
            "--uts",
            # NOT --ipc, much as the IPC isolation is wanted: it makes enroot's `10-devices` hook
            # rebuild /dev, and that hook bind-mounts /dev/log with no `nofail`, so it hard-fails on
            # any host without a syslog socket — which is every containerised agent. The part of
            # --ipc that actually matters here (a per-container /dev/shm) is done below instead.
            "--rw",
            "-m",
            f"{gate_dir}:{_GATE_MNT}:none:x-create=auto,bind,rw",
            # enroot's default fstab BINDS the host's /dev/shm into every container, so all kernels
            # on a node share one /dev/shm — they see each other's segments and compete for its
            # size. Give each its own tmpfs, sized from the session's `shmem` resource_opt (Docker's
            # ShmSize) and defaulting to Docker's 64 MiB. Later -m entries win, so this overrides
            # the fstab bind.
            "-m",
            (
                f"tmpfs:/dev/shm:tmpfs:x-create=dir,rw,nosuid,nodev,mode=1777,"
                f"size={int(spec.get('shmem') or _DEFAULT_SHM_BYTES)}"
            ),
        ]
        # Host binds from the OCI spec (scratch config/work, krunner, vfolders, /etc/hosts, ...).
        # enroot provides proc/sys/dev/tmpfs itself (userns), so those are skipped.
        for mount in spec.get("mounts", []):
            src, dst = mount.get("source"), mount.get("destination")
            if not src or not dst:
                continue
            mtype = mount.get("type")
            opts = mount.get("options") or []
            if mtype in _SKIP_MOUNT_TYPES:
                continue
            if mtype not in (None, "bind", "rbind") and not ({"bind", "rbind"} & set(opts)):
                continue
            # `readonly` is how the runtime-neutral descriptor (mount_to_oci) spells it; `options`
            # is the OCI runtime-spec spelling. Honor both — dropping it would silently hand the
            # kernel a writable krunner and writable read-only vfolders.
            mode = "ro" if mount.get("readonly") or "ro" in opts else "rw"
            argv += ["-m", f"{src}:{dst}:none:x-create=auto,bind,{mode}"]
        # /dev node passthrough (AMD ROCm, NPUs, InfiniBand HCAs). runc grants these via the device
        # cgroup; a rootless userns cannot mknod, so the existing host node is bind-mounted instead
        # — which is all an already-created device node needs.
        for device in spec.get("devices", []):
            src, dst = device.get("source"), device.get("destination") or device.get("source")
            if not src:
                continue
            argv += ["-m", f"{src}:{dst}:none:x-create=auto,bind,rw"]
        # The kernel's environment. The containerd agent merges every compute plugin's env into
        # `spec["env"]`, and enroot's hooks read the container env file this builds — so an
        # accelerator's wiring (NVIDIA_*) only takes effect if it is forwarded here. It is NOT
        # enough that the same variables reach the in-container runner via /home/config/environ.txt:
        # the hooks run before the container's command does.
        env = {str(k): str(v) for k, v in (spec.get("env") or {}).items()}
        # NVIDIA: enroot's `98-nvidia` hook shells out to nvidia-container-cli driven by
        # NVIDIA_VISIBLE_DEVICES. The scheduler's allocation is authoritative — pin exactly the
        # GPUs assigned to this kernel, and "void" (the hook's own no-op sentinel) when none, so a
        # CPU-only kernel on a GPU node gets no device.
        gpus = spec.get("gpus") or []
        env["NVIDIA_VISIBLE_DEVICES"] = ",".join(str(g) for g in gpus) if gpus else "void"
        if gpus:
            env.setdefault("NVIDIA_DRIVER_CAPABILITIES", "all")
        # The kernel-runner must stay **container-root**, which `--root` maps to the host kernel uid
        # (the scratch owner). If it instead dropped to a non-zero LOCAL_USER_ID, that container uid
        # would be unmapped in the rootless userns (-> nobody) and could not read the scratch it owns
        # on the host. So force LOCAL_USER_ID/GID to 0: the runner runs as container-root == the host
        # kernel uid, files it creates land under the kernel uid on the host exactly as intended, and
        # sshd/jupyter/`su-exec` all succeed. Drop any LOCAL_USER_ID/GID the base injected.
        env["LOCAL_USER_ID"] = "0"
        env["LOCAL_GROUP_ID"] = "0"
        for key, value in env.items():
            # enroot's env file is line-oriented (`key=value`); a multi-line value would corrupt it
            # and silently shift every later variable. The runner still sees it via environ.txt.
            if "\n" in value:
                log.warning("[enroot] dropping multi-line env var {} from the container env", key)
                continue
            argv += ["-e", f"{key}={value}"]
        # The pause-wrapper is the container command; the real command follows as its args.
        argv += [container_id, f"{_GATE_MNT}/pause.sh", *self._commands.get(container_id, ())]
        # Hardening: capabilities + AppArmor are dropped (userns scopes caps; enroot has no
        # AppArmor). Syscall filtering is delegated to BAI's `jail` sandbox rather than OCI seccomp,
        # which is a runc feature enroot cannot provide — see _log_hardening_disposition.
        return argv

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
        if self._agent_netns is None:
            self._agent_netns = self._netns_id(os.getpid())
        poll_interval = 0.1
        for _ in range(max(1, int(_TASK_START_TIMEOUT_SEC / poll_interval))):
            if proc.returncode is not None:
                raise RuntimeError(f"enroot start exited early (rc={proc.returncode})")
            for pid in self._descendant_pids(proc.pid):
                ns = self._netns_id(pid)
                if ns is not None and ns != self._agent_netns:
                    return pid
            await asyncio.sleep(poll_interval)
        raise TimeoutError("enroot container did not reach its netns'd pause within timeout")

    async def _reap(self, container_id: str) -> None:
        proc = self._procs.pop(container_id, None)
        if proc is not None and proc.returncode is None:
            proc.kill()
            await proc.wait()

    @override
    async def kill_container(
        self, container_id: str, *, signal: int, all_processes: bool = True
    ) -> None:
        pid = self._pids.get(container_id)
        if pid is None:
            return
        # all_processes -> signal the process group (enroot start's tree); else the init PID only.
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
        await self._run(_ENROOT_BIN, "remove", "--force", container_id)
        # The log is as much part of the container as its rootfs — the containerd runtime unlinks it
        # here too. The rotated siblings go with it: leaving them would keep a terminated kernel's
        # log on disk forever, since nothing else ever revisits that path.
        await asyncio.to_thread(unlink_log_files, self._log_path(container_id))
        # ...and the two-phase gate (pause.sh + the `go` FIFO) under the per-container state dir.
        await asyncio.to_thread(shutil.rmtree, self._state_path / container_id, ignore_errors=True)
        await asyncio.to_thread(self._remove_cgroup, container_id)
        self._specs.pop(container_id, None)
        self._commands.pop(container_id, None)
        self._pids.pop(container_id, None)
        self._images.pop(container_id, None)
        self._labels.pop(container_id, None)

    @override
    async def commit_container(
        self,
        container_id: str,
        *,
        base_image_ref: str,
        target_ref: str,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        # enroot's analog of a rootfs snapshot is `enroot export` (produces a new .sqsh).
        rc, _out, err = await self._run(
            _ENROOT_BIN, "export", "--output", str(self._sqsh(target_ref)), container_id
        )
        if rc != 0:
            raise RuntimeError(
                f"enroot export failed for {container_id}: {err.decode(errors='replace')}"
            )
        self._meta(target_ref).write_text(
            json.dumps({
                "ref": target_ref,
                "digest": None,
                "config_digest": None,
                "architecture": "",
                "labels": dict(labels or {}),
                "entrypoint": None,
            })
        )

    # ------------------------------------------------------------------ introspection
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

    @override
    async def list_containers(self) -> Sequence[str]:
        return list(self._pids.keys())

    @override
    async def list_container_infos(self) -> Sequence[ContainerInfo]:
        # In-memory tracking, but it survives an agent restart: open() rebuilds it from the
        # per-container journal (enroot has no label store or container-list API that carries our
        # labels, so the runtime has to keep that map itself). See _record_container.
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
    async def subscribe_task_events(self) -> AsyncIterator[TaskEvent]:
        # No daemon event stream; poll tracked PIDs and emit 'exit' when one disappears.
        seen = dict(self._pids)
        while True:
            await asyncio.sleep(1.0)
            for cid, pid in list(seen.items()):
                if not self._alive(pid):
                    seen.pop(cid, None)
                    yield TaskEvent(kind="exit", container_id=cid, exit_code=0)
            for cid, pid in self._pids.items():
                seen.setdefault(cid, pid)

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
        # No daemon exec; enter the enroot process's mount+pid+user namespaces via nsenter.
        # (Only caller today is sudoers provisioning + the file APIs' container-side view.)
        pid = self._pids.get(container_id)
        if pid is None:
            raise RuntimeError(f"no live task for {container_id}")
        nsenter = ["nsenter", "-t", str(pid), "-m", "-p", "-U", "--preserve-credentials"]
        if cwd is not None:
            nsenter += ["--wd", cwd]
        rc, out, err = await asyncio.wait_for(self._run(*nsenter, "--", *args), timeout=timeout_sec)
        return ExecResult(exit_code=rc, stdout=out, stderr=err)
