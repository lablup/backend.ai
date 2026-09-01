"""``PodmanRuntime`` — the **podman** backend's rootless OCI runtime.

Podman is the one rootless runtime here that brings its own monitor. ``conmon`` reparents the
container, holds its stdio, enforces the log size cap and keeps a container record that outlives
the agent, so everything :class:`~ai.backend.agent.rootless.base.SelfHostedRootlessRuntime` exists
to provide — the PID journal, the process handle, the reap loop, the log rotator — is already
there. This class implements the rootless contract
(:class:`~ai.backend.agent.rootless.runtime.RootlessOciRuntime`) directly and lets podman do the
rest.

What podman does NOT give us is the two-phase start: ``podman start`` execs the container's
command immediately, with no window in which its netns exists but the workload has not run. So the
same gate the other rootless backends use is used here (see
:mod:`ai.backend.agent.rootless.gate`) — the container's entrypoint is a wrapper that parks in the
final namespaces and execs the real command on a FIFO. Measured: the PID conmon reports before the
release is the PID the workload runs under afterwards, and the container's netns is owned by the
invoking uid, which is what the privnet requires before it will attach a veth.

Nor does it place the container where the agent's stats reader looks. Rootless podman resolves
``--cgroup-parent`` inside the user's own delegated subtree, and the kernel's common-ancestor rule
means an unprivileged process cannot move anything into ``/sys/fs/cgroup/backend-ai/<kernel-id>``
even when that directory is writable. So confinement goes the same way it does for the other
rootless backends: through the privnet, while the container is still held at its gate.
"""

from __future__ import annotations

import asyncio
import gzip
import json
import logging
import os
import shutil
from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, Final, override

from ai.backend.agent.containerd.runtime.interface import (
    ContainerInfo,
    ExecResult,
    ImageInfo,
    TaskEvent,
    TaskHandle,
)
from ai.backend.agent.containerd.runtime.spec import container_cgroup_fs_path
from ai.backend.agent.errors.agent import ContainerConfinementFailedError
from ai.backend.agent.rootless.gate import GATE_MNT, signal_go, wait_ready, write_gate
from ai.backend.agent.rootless.registry import is_insecure_registry
from ai.backend.agent.rootless.runtime import RootlessOciRuntime
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_PODMAN_BIN: Final = "podman"
# Docker's default ShmSize, used when the session did not ask for one.
DEFAULT_SHM_BYTES: Final = 64 * 1024 * 1024
# How long create_task waits for the container to reach its gate.
TASK_START_TIMEOUT_SEC: Final = 30.0
# How much of the container log a failed launch carries into its exception.
_LAUNCH_DIAGNOSIS_LINES: Final = 15
# podman applies the container's seccomp profile and gives it a private IPC namespace itself, so
# unlike the self-hosted backends the wrapper has nothing to install — it only has to park.
PAUSE_SCRIPT: Final = f"""#!/bin/sh
: > {GATE_MNT}/ready
read _ < {GATE_MNT}/go 2>/dev/null
exec "$@"
"""
# OCI mount types podman provides itself in a userns — never forwarded as host binds.
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


class PodmanRuntime(RootlessOciRuntime):
    """Session containers through the podman CLI. See the module docstring."""

    backend_name: ClassVar[str] = "podman"

    # container_id -> the OCI spec handed to create_container (re-read at start/confine time).
    _specs: dict[str, Mapping[str, Any]]
    # Where the agent's log reader expects a container's log, and the total budget for it.
    # Both are None/0 until configure_logging runs, which is after open().
    _log_root: Path | None
    _log_max_bytes: int

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._specs = {}
        self._log_root = None
        self._log_max_bytes = 0

    # ------------------------------------------------------------------ lifecycle
    @override
    async def open(self) -> None:
        for path in (self._data_path, self._cache_path, self._runtime_path, self._state_path):
            path.mkdir(parents=True, exist_ok=True)
        # podman is run as the kernel uid (see _uid_drop_prefix), so its stores must belong to it.
        self._own_existing_artifacts()

    @override
    async def close(self) -> None:
        pass

    def _own_existing_artifacts(self) -> None:
        if os.geteuid() == self._kernel_uid:
            return
        for path in (self._data_path, self._cache_path, self._runtime_path, self._state_path):
            try:
                os.chown(path, self._kernel_uid, self._kernel_gid)
            except OSError as e:
                log.warning("[podman] cannot hand {} to the kernel uid: {!r}", path, e)

    @override
    def _runtime_env(self) -> dict[str, str]:
        # podman rootless keeps per-user state under $HOME and $XDG_RUNTIME_DIR. Left to the
        # agent's own environment those would be the agent user's, which is the wrong uid the
        # moment the launch drops to the kernel uid — and on a containerised agent $HOME may not
        # be writable at all. Anchor everything to the agent's var-base-path instead.
        home = self._state_path / "home"
        xdg_runtime = self._runtime_path / "xdg"
        for path, mode in ((home, 0o700), (xdg_runtime, 0o700)):
            path.mkdir(parents=True, exist_ok=True, mode=mode)
            if os.geteuid() != self._kernel_uid:
                try:
                    os.chown(path, self._kernel_uid, self._kernel_gid)
                except OSError:
                    pass
        return {
            "HOME": str(home),
            "XDG_RUNTIME_DIR": str(xdg_runtime),
            "XDG_DATA_HOME": str(self._data_path / "share"),
            "XDG_CONFIG_HOME": str(self._data_path / "config"),
        }

    def _global_argv(self) -> list[str]:
        return [
            _PODMAN_BIN,
            # The image store and the per-container runtime state, under the agent's var dir
            # rather than the invoking user's home.
            "--root",
            str(self._data_path / "storage"),
            "--runroot",
            str(self._runtime_path / "storage"),
            # The systemd cgroup manager needs a user session bus, which an agent started as a
            # service does not have. Nothing is lost: the container is moved into the agent's own
            # cgroup hierarchy immediately afterwards (see _confine).
            "--cgroup-manager=cgroupfs",
        ]

    async def _podman(
        self, *args: str, extra_env: Mapping[str, str] | None = None
    ) -> tuple[int, bytes, bytes]:
        return await self._run(*self._global_argv(), *args, extra_env=extra_env)

    async def _podman_json(self, *args: str) -> Any:
        rc, out, err = await self._podman(*args)
        if rc != 0:
            raise RuntimeError(f"podman {' '.join(args)} failed: {err.decode(errors='replace')}")
        try:
            return json.loads(out or b"[]")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"podman {' '.join(args)} returned no usable JSON: {e}") from e

    # ------------------------------------------------------------------ images
    def _tls_argv(self, image_ref: str) -> list[str]:
        # `--tls-verify=false` does not pin http the way enroot's ENROOT_ALLOW_HTTP does; podman
        # still tries https first. It is still scoped to the registries the operator's certs.d
        # actually describes as insecure, so a public registry is never contacted with verification
        # turned off.
        return (
            ["--tls-verify=false"]
            if is_insecure_registry(image_ref, self._registry_hosts_dir)
            else []
        )

    @staticmethod
    def _creds_argv(auth: Mapping[str, str] | None) -> list[str]:
        if not auth or not auth.get("username"):
            return []
        return ["--creds", f"{auth.get('username')}:{auth.get('password', '')}"]

    @override
    async def image_exists(self, image_ref: str) -> bool:
        rc, _out, _err = await self._podman("image", "exists", image_ref)
        return rc == 0

    @override
    async def image_digest(self, image_ref: str) -> str | None:
        rc, out, _err = await self._podman("image", "inspect", "--format", "{{.Digest}}", image_ref)
        return out.decode().strip() or None if rc == 0 else None

    @override
    async def image_config_digest(self, image_ref: str) -> str | None:
        rc, out, _err = await self._podman("image", "inspect", "--format", "{{.Id}}", image_ref)
        if rc != 0:
            return None
        image_id = out.decode().strip()
        if not image_id:
            return None
        return image_id if image_id.startswith("sha256:") else f"sha256:{image_id}"

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        rc, _out, err = await self._podman(
            "pull", *self._tls_argv(image_ref), *self._creds_argv(auth), image_ref
        )
        if rc != 0:
            raise RuntimeError(
                f"podman pull failed for {image_ref}: {err.decode(errors='replace')}"
            )

    @override
    async def list_images(self) -> Sequence[str]:
        return [info.name for info in await self.list_image_infos()]

    @override
    async def list_image_infos(self) -> Sequence[ImageInfo]:
        rows = await self._podman_json("images", "--format", "json")
        infos: list[ImageInfo] = []
        for row in rows or []:
            labels = {str(k): str(v) for k, v in (row.get("Labels") or {}).items()}
            # One stored image can carry several tags; the agent's scan is per reference.
            for name in row.get("Names") or []:
                infos.append(
                    ImageInfo(
                        name=str(name),
                        digest=str(row.get("Digest") or ""),
                        architecture=str(row.get("Arch") or ""),
                        labels=labels,
                    )
                )
        if infos and not infos[0].architecture:
            # `podman images` does not report the architecture; it lives in the image config.
            infos = [
                ImageInfo(
                    name=info.name,
                    digest=info.digest,
                    architecture=await self._image_arch(info.name),
                    labels=info.labels,
                )
                for info in infos
            ]
        return infos

    async def _image_arch(self, image_ref: str) -> str:
        rc, out, _err = await self._podman(
            "image", "inspect", "--format", "{{.Architecture}}", image_ref
        )
        return out.decode().strip() if rc == 0 else ""

    @override
    async def remove_image(self, image_ref: str, *, sync: bool = False) -> None:
        rc, _out, err = await self._podman("rmi", "--force", image_ref)
        if rc != 0:
            raise RuntimeError(f"podman rmi failed for {image_ref}: {err.decode(errors='replace')}")

    @override
    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        rc, _out, err = await self._podman(
            "push", *self._tls_argv(image_ref), *self._creds_argv(auth), image_ref
        )
        if rc != 0:
            raise RuntimeError(
                f"podman push failed for {image_ref}: {err.decode(errors='replace')}"
            )

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        staged = self._cache_path / f"{dest_path.name}.tar"
        staged.parent.mkdir(parents=True, exist_ok=True)
        rc, _out, err = await self._podman(
            "save", "--format", "oci-archive", "--output", str(staged), image_ref
        )
        if rc != 0:
            staged.unlink(missing_ok=True)
            raise RuntimeError(
                f"podman save failed for {image_ref}: {err.decode(errors='replace')}"
            )
        try:
            await asyncio.to_thread(self._gzip_into, staged, dest_path)
        finally:
            staged.unlink(missing_ok=True)

    @staticmethod
    def _gzip_into(src: Path, dest: Path) -> None:
        with src.open("rb") as fin, gzip.open(dest, "wb") as fout:
            shutil.copyfileobj(fin, fout)

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        rc, out, _err = await self._podman(
            "image", "inspect", "--format", "{{json .Config}}", image_ref
        )
        if rc != 0:
            return None
        try:
            config = json.loads(out or b"{}")
        except json.JSONDecodeError:
            return None
        entrypoint = config.get("Entrypoint") or config.get("Cmd")
        return [str(a) for a in entrypoint] if entrypoint else None

    # ------------------------------------------------------------------ container lifecycle
    def _gate_dir(self, container_id: str) -> Path:
        return self._state_path / container_id / "gate"

    def _log_path(self, container_id: str) -> Path:
        # Must agree with the agent's reader (containerd.runtime.grpc.container_log_path).
        if self._log_root is not None:
            return self._log_root / f"{container_id}.log"
        return self._state_path / container_id / "container.log"

    @override
    def configure_logging(self, launcher: Path, log_root: Path, max_total_bytes: int) -> None:
        # conmon writes and caps the log itself, so the `launcher` (containerd's binary:// writer)
        # has nobody to start it here and no rotator is needed on our side. Measured: a 1 MB cap
        # held a container that wrote 4 MiB to 842 KB. conmon caps the single active file rather
        # than keeping rotated siblings, so the whole budget goes to it.
        self._log_root = log_root
        self._log_max_bytes = max_total_bytes

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
        self._specs[container_id] = oci_spec
        self._labels[container_id] = dict(oci_spec.get("labels") or {})
        gate_dir = self._gate_dir(container_id)
        await asyncio.to_thread(
            write_gate, gate_dir, PAUSE_SCRIPT, uid=self._kernel_uid, gid=self._kernel_gid
        )
        argv = self._create_argv(container_id, image_ref, command, oci_spec, gate_dir)
        rc, _out, err = await self._podman(*argv, extra_env=self._launch_env(oci_spec))
        if rc != 0:
            raise RuntimeError(
                f"podman create failed for {container_id}: {err.decode(errors='replace')}"
            )

    def _create_argv(
        self,
        container_id: str,
        image_ref: str,
        command: Sequence[str],
        spec: Mapping[str, Any],
        gate_dir: Path,
    ) -> list[str]:
        argv = [
            "create",
            "--name",
            container_id,
            # The netns is ours to fill: the privnet attaches a veth to it after the gate. Letting
            # podman set up a network would both need netavark and put a second interface in.
            "--network=none",
            # A rootless podman maps container-root to the invoking uid, which _uid_drop_prefix
            # makes the kernel uid — the owner of the scratch. So the kernel-runner stays
            # container-root and reads what it owns with no host privilege and no remapping.
            "--user=0:0",
            "--mount",
            f"type=bind,src={gate_dir},dst={GATE_MNT},rw",
            "--entrypoint",
            json.dumps([f"{GATE_MNT}/pause.sh"]),
            "--shm-size",
            str(int(spec.get("shmem") or DEFAULT_SHM_BYTES)),
        ]
        if hostname := spec.get("hostname"):
            argv += ["--hostname", str(hostname)]
        if self._log_root is not None:
            argv += [
                "--log-driver",
                "k8s-file",
                "--log-opt",
                f"path={self._log_path(container_id)}",
            ]
            if self._log_max_bytes:
                argv += ["--log-opt", f"max-size={self._log_max_bytes}"]
        argv += self._security_argv(container_id, spec)
        for key, value in (spec.get("labels") or {}).items():
            argv += ["--label", f"{key}={value}"]
        for mount in spec.get("mounts", []):
            src, dst = mount.get("source"), mount.get("destination")
            if not src or not dst:
                continue
            mtype = mount.get("type")
            opts = mount.get("options") or []
            if mtype in SKIP_MOUNT_TYPES:
                continue
            if mtype not in (None, "bind", "rbind") and not ({"bind", "rbind"} & set(opts)):
                continue
            # `readonly` is the runtime-neutral descriptor's spelling, `options` the OCI one.
            # Honouring only one would silently hand the kernel a writable krunner and writable
            # read-only vfolders.
            mode = "ro" if mount.get("readonly") or "ro" in opts else "rw"
            argv += ["--mount", f"type=bind,src={src},dst={dst},{mode}"]
        for device in spec.get("devices", []):
            src = device.get("source")
            if not src:
                continue
            argv += ["--device", f"{src}:{device.get('destination') or src}:rwm"]
        for key, value in (spec.get("env") or {}).items():
            # The kernel-runner must stay container-root, which the rootless userns maps to the
            # host kernel uid (the scratch owner). A non-zero LOCAL_USER_ID would be unmapped
            # inside the namespace and could not read the scratch it owns on the host.
            if key in ("LOCAL_USER_ID", "LOCAL_GROUP_ID"):
                continue
            argv += ["--env", f"{key}={value}"]
        argv += ["--env", "LOCAL_USER_ID=0", "--env", "LOCAL_GROUP_ID=0"]
        # The wrapper is the entrypoint; the real command is its argument, exec'd on release.
        argv += [image_ref, *command]
        return argv

    def _security_argv(self, container_id: str, spec: Mapping[str, Any]) -> list[str]:
        argv = ["--security-opt", "no-new-privileges"]
        oci_seccomp = spec.get("seccomp")
        if not oci_seccomp:
            # The operator chose the jail sandbox, so the agent generated no profile. Unlike the
            # self-hosted backends, leaving it out here does not mean unconfined: podman applies
            # its own default profile.
            log.info(
                "[podman] no seccomp profile for container {} — podman's default profile applies"
                " (sandbox_type=jail)",
                container_id,
            )
            return argv
        profile = self._state_path / container_id / "seccomp.json"
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.write_text(json.dumps(oci_seccomp))
        if os.geteuid() != self._kernel_uid:
            os.chown(profile, self._kernel_uid, self._kernel_gid)
        return argv + ["--security-opt", f"seccomp={profile}"]

    @override
    async def create_task(self, container_id: str, *, use_logger: bool = True) -> TaskHandle:
        """Start the container and hold it at its gate, confined, with an attachable netns."""
        gate_dir = self._gate_dir(container_id)
        rc, _out, err = await self._podman("start", container_id)
        if rc != 0:
            raise RuntimeError(
                f"podman start failed for {container_id}: {err.decode(errors='replace')}"
            )
        try:
            async with asyncio.timeout(TASK_START_TIMEOUT_SEC):
                await wait_ready(gate_dir, failure=lambda: None)
        except TimeoutError:
            raise TimeoutError(
                f"podman container did not reach the pause (no ready marker):"
                f"{self._launch_diagnosis(container_id)}"
            ) from None
        pid = await self.container_pid(container_id)
        if pid is None:
            raise RuntimeError(
                f"podman reported no pid for {container_id} after it reached its gate:"
                f"{self._launch_diagnosis(container_id)}"
            )
        await self._confine(container_id, self._specs.get(container_id, {}), pid)
        return TaskHandle(container_id=container_id, pid=pid)

    def _launch_diagnosis(self, container_id: str) -> str:
        """The tail of what the container printed while failing to reach its gate.

        conmon owns the container's stdio, so a bare "it never got there" is all the caller would
        otherwise see — and that says nothing about whether the image, the userns or a missing
        subuid mapping was the problem. Best-effort: a diagnosis must never mask the failure it
        describes.
        """
        try:
            text = self._log_path(container_id).read_text(errors="replace")
        except OSError:
            return ""
        tail = [line for line in text.splitlines() if line.strip()][-_LAUNCH_DIAGNOSIS_LINES:]
        return ("\n" + "\n".join(tail)) if tail else ""

    async def _confine(self, container_id: str, spec: Mapping[str, Any], top_pid: int) -> None:
        """Put the container in the cgroup the agent's stats reader reads, with its limits.

        Only the gated process exists at this point and everything it forks inherits the cgroup, so
        one move confines the whole workload — no process-tree walk, unlike the self-hosted
        backends where the agent has already spawned a launch tree of its own.

        Rootless podman cannot do this itself: it resolves ``--cgroup-parent`` inside the user's
        delegated subtree, and the kernel's common-ancestor rule blocks an unprivileged move into
        ``/sys/fs/cgroup/backend-ai`` even where that directory is writable. So it goes to the
        privnet, exactly as the other rootless backends' does.
        """
        if self._privnet_socket:
            await self._confine_via_privnet(container_id, spec, top_pid)
            return
        cgroup = self._create_cgroup(container_id, spec)
        if cgroup is None:
            return  # cgroup v1 host: a standing property of the node, not a failed attempt
        try:
            await asyncio.to_thread((cgroup / "cgroup.procs").write_text, str(top_pid))
        except OSError as e:
            raise ContainerConfinementFailedError(
                f"cannot move {container_id} into {cgroup} ({e!r}); refusing to start a kernel"
                " that would run without the CPU and memory it was allocated"
            ) from e

    @override
    async def start_task(self, container_id: str) -> None:
        await asyncio.to_thread(signal_go, self._gate_dir(container_id))

    @override
    async def kill_container(
        self, container_id: str, *, signal: int, all_processes: bool = True
    ) -> None:
        # `podman kill` signals the container's init process only. Broadcasting to the whole
        # container is what the cgroup is for -- and the cgroup is the agent's here, not podman's
        # (see _confine), so the broadcast is done through it rather than through podman.
        if all_processes:
            await asyncio.to_thread(self._signal_cgroup, container_id, signal)
            return
        await self._podman("kill", "--signal", str(signal), container_id)

    def _signal_cgroup(self, container_id: str, signum: int) -> None:
        cgroup = container_cgroup_fs_path(container_id)
        try:
            pids = [int(line) for line in (cgroup / "cgroup.procs").read_text().split()]
        except OSError:
            pids = []
        for pid in pids:
            try:
                os.kill(pid, signum)
            except (ProcessLookupError, PermissionError):
                continue

    @override
    async def stop_container(self, container_id: str, *, grace_period: float) -> None:
        await self._podman("stop", "--time", str(int(grace_period)), container_id)

    @override
    async def remove_container(self, container_id: str) -> None:
        await self._podman("rm", "--force", container_id)
        if self._privnet_socket:
            await self._release_via_privnet(container_id)
        else:
            await asyncio.to_thread(self._remove_cgroup, container_id)
        self._specs.pop(container_id, None)
        self._labels.pop(container_id, None)
        shutil.rmtree(self._state_path / container_id, ignore_errors=True)

    @override
    async def commit_container(
        self,
        container_id: str,
        *,
        base_image_ref: str,
        target_ref: str,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        argv = ["commit", "--format", "docker"]
        for key, value in (labels or {}).items():
            argv += ["--change", f"LABEL {key}={value}"]
        rc, _out, err = await self._podman(*argv, container_id, target_ref)
        if rc != 0:
            raise RuntimeError(
                f"podman commit failed for {container_id}: {err.decode(errors='replace')}"
            )

    # ------------------------------------------------------------------ introspection
    @override
    async def list_containers(self) -> Sequence[str]:
        return [info.id for info in await self.list_container_infos()]

    @override
    async def list_container_infos(self) -> Sequence[ContainerInfo]:
        rows = await self._podman_json("ps", "--all", "--format", "json")
        infos: list[ContainerInfo] = []
        for row in rows or []:
            names = row.get("Names") or []
            if not names:
                continue  # created by something that is not this agent; it has no id we know
            infos.append(
                ContainerInfo(
                    id=str(names[0]),
                    image=str(row.get("Image") or ""),
                    labels={str(k): str(v) for k, v in (row.get("Labels") or {}).items()},
                    status=str(row.get("State") or ""),
                )
            )
        return infos

    @override
    async def container_pid(self, container_id: str) -> int | None:
        rc, out, _err = await self._podman("inspect", "--format", "{{.State.Pid}}", container_id)
        if rc != 0:
            return None
        try:
            pid = int(out.decode().strip() or 0)
        except ValueError:
            return None
        return pid or None

    @override
    async def container_status(self, container_id: str) -> str | None:
        rc, out, _err = await self._podman("inspect", "--format", "{{.State.Status}}", container_id)
        if rc != 0:
            return None
        return out.decode().strip() or None

    @override
    async def subscribe_task_events(self) -> AsyncIterator[TaskEvent]:
        """conmon's own event stream, which is the thing the self-hosted backends have to poll for.

        The stream ends when the podman process does; the caller re-subscribes.
        """
        proc = await asyncio.create_subprocess_exec(
            *self._uid_drop_prefix(),
            *self._global_argv(),
            "events",
            "--filter",
            "type=container",
            "--format",
            "json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env=self._process_env(),
        )
        stdout = proc.stdout
        if stdout is None:  # PIPE was requested, so this cannot happen -- but mypy cannot know
            raise RuntimeError("podman events produced no stream to read")
        try:
            async for line in stdout:
                event = self._parse_event(line)
                if event is not None:
                    yield event
        finally:
            if proc.returncode is None:
                proc.kill()
            await proc.wait()

    @staticmethod
    def _parse_event(line: bytes) -> TaskEvent | None:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return None
        name = str(row.get("Name") or "")
        if not name:
            return None
        match str(row.get("Status") or ""):
            case "start":
                return TaskEvent(kind="start", container_id=name)
            case "died":
                return TaskEvent(
                    kind="exit", container_id=name, exit_code=int(row.get("ContainerExitCode") or 0)
                )
            case "oom":
                return TaskEvent(kind="oom", container_id=name)
            case _:
                return None

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
        argv = ["exec"]
        if uid is not None:
            argv += ["--user", f"{uid}:{gid}" if gid is not None else str(uid)]
        if cwd is not None:
            argv += ["--workdir", cwd]
        proc = await asyncio.create_subprocess_exec(
            *self._uid_drop_prefix(),
            *self._global_argv(),
            *argv,
            container_id,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._process_env(),
        )
        try:
            async with asyncio.timeout(timeout_sec):
                stdout, stderr = await proc.communicate()
        except TimeoutError:
            # Kill it rather than leave it: a hung exec would otherwise pin the agent's caller for
            # as long as the command runs.
            proc.kill()
            await proc.wait()
            raise TimeoutError(
                f"exec in {container_id} did not finish within {timeout_sec}s: {' '.join(args)}"
            ) from None
        return ExecResult(exit_code=proc.returncode or 0, stdout=stdout, stderr=stderr)
