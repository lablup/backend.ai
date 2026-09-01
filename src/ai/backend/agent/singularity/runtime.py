"""``SingularityRuntime`` — the **apptainer / singularity** backend's rootless OCI runtime.

Everything a daemonless rootless runtime owes the agent — cgroups, the container journal, log
rotation, death events, the two-phase attachable-netns gate, seccomp — comes from
:class:`~ai.backend.agent.rootless.base.SelfHostedRootlessRuntime`. What is apptainer's, and so lives
here:

* **Images** are ``--sandbox`` directories (``<slug>.sbx``) rather than a single archive, with the
  same JSON sidecar the enroot backend uses to carry the identity a directory cannot: config
  digest, kernel-spec / base-distro labels, and the base's entrypoint/cmd/env/workdir. SIF is
  deliberately avoided — it needs FUSE to mount, and a sandbox directory does not.
* **Per-container writes go to an overlay**, not a copy. The image sandbox stays shared and
  read-only; each container gets `upper/` + `work/`. Creating a container is two ``mkdir``s, where
  the enroot backend has to unpack a whole squashfs per kernel.
* **The launch line**, whose flags are not interchangeable with enroot's — see ``_launch_argv``.

Measured on apptainer 1.5.3, unprivileged (no ``starter-suid``), as uid 1000.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import shutil
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, Final, override

from ai.backend.agent.containerd.runtime.interface import ImageInfo
from ai.backend.agent.rootless.base import (
    GATE_MNT,
    SKIP_MOUNT_TYPES,
    SelfHostedRootlessRuntime,
    force_rmtree,
    write_layer,
)
from ai.backend.agent.rootless.registry import fetch_image_metadata, is_insecure_registry
from ai.backend.agent.rootless.registry import push_image as fetch_push
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

# Apptainer installs a `singularity` alias, and SingularityCE ships only the latter. Prefer the
# maintained name and fall back, so one backend serves both forks.
_BIN_CANDIDATES: Final = ("apptainer", "singularity")
_SLUG_RE: Final = re.compile(r"[^A-Za-z0-9_.-]+")


def _slug(image_ref: str) -> str:
    return _SLUG_RE.sub("+", image_ref)


def resolve_binary() -> str:
    for candidate in _BIN_CANDIDATES:
        if shutil.which(candidate):
            return candidate
    # Fall through to the preferred name so the failure names the missing tool rather than
    # surfacing as a bare FileNotFoundError from create_subprocess_exec.
    return _BIN_CANDIDATES[0]


_OVERLAY_XATTR_PREFIXES: Final = ("trusted.overlay.", "user.overlay.", "user.fuseoverlayfs.")


def _is_opaque(path: Path) -> bool:
    for prefix in _OVERLAY_XATTR_PREFIXES:
        with contextlib.suppress(OSError):
            if os.getxattr(path, f"{prefix}opaque") == b"y":
                return True
    return False


def _clone_metadata(src: Path, dst: Path) -> None:
    """Owner, mode and mtime from src onto dst, minus the overlay's own bookkeeping xattrs."""
    info = src.lstat()
    with contextlib.suppress(OSError):
        os.chown(dst, info.st_uid, info.st_gid, follow_symlinks=False)
    if not dst.is_symlink():
        with contextlib.suppress(OSError):
            dst.chmod(stat.S_IMODE(info.st_mode))
        with contextlib.suppress(OSError):
            os.utime(dst, (info.st_atime, info.st_mtime))
    with contextlib.suppress(OSError):
        for name in os.listxattr(dst, follow_symlinks=False):
            if name.startswith(_OVERLAY_XATTR_PREFIXES):
                with contextlib.suppress(OSError):
                    os.removexattr(dst, name, follow_symlinks=False)


def _copy_entry(src: Path, dst: Path) -> None:
    if dst.is_dir() and not dst.is_symlink():
        force_rmtree(dst)
    else:
        dst.unlink(missing_ok=True)
    if src.is_symlink():
        dst.symlink_to(src.readlink())
    else:
        shutil.copy2(src, dst, follow_symlinks=False)
    _clone_metadata(src, dst)


# Not "all": apptainer validates this against its own capability list and aborts the whole launch
# on anything it does not recognise -- measured, `NVIDIA_DRIVER_CAPABILITIES=all` yields
# `FATAL: container creation failed: unknown NVIDIA_DRIVER_CAPABILITIES value: all`. (The enroot
# hook, and nvidia-container-cli directly, do accept "all".) These two are what a compute kernel
# needs: the CUDA driver, and the nvidia-smi/NVML tooling that reports on it.
NVIDIA_CAPABILITIES: Final = "compute,utility"


class SingularityRuntime(SelfHostedRootlessRuntime):
    backend_name: ClassVar[str] = "singularity"

    _binary: str

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._binary = resolve_binary()

    @override
    async def open(self) -> None:
        await super().open()
        # apptainer refuses to build if APPTAINER_TMPDIR does not already exist — it will not
        # create it — and the failure surfaces as a pull error naming a path, with nothing to say
        # that the agent was supposed to have made it. The base creates the four roots; this one
        # is a child of the cache root, so it has to be created here.
        tmp = self._tmp_path()
        await asyncio.to_thread(tmp.mkdir, parents=True, exist_ok=True)
        if os.geteuid() != self._kernel_uid:
            os.chown(tmp, self._kernel_uid, self._kernel_gid)

    def _tmp_path(self) -> Path:
        return self._cache_path / "tmp"

    @override
    def _launch_env(self, spec: Mapping[str, Any]) -> dict[str, str]:
        """The GPU allocation, in **apptainer's own** environment.

        ``--nvccli`` hands the injection to nvidia-container-cli, and apptainer builds that call
        from the variables in its *own* process environment -- not from the ``--env`` values, which
        only land inside the container where nvccli never looks. The shared `_process_env` strips
        ``NVIDIA_*`` (right for enroot, whose hook reads the container's env file), so without this
        the runtime is launched with no allocation at all: measured, the container then comes up
        with `/dev/nvidiactl` and nothing else, `nvidia-smi` reports "No devices were found", and
        `cuInit` returns 100 (CUDA_ERROR_NO_DEVICE) -- a GPU session that silently has no GPU.
        """
        gpus = [str(g) for g in (spec.get("gpus") or [])]
        if not gpus:
            return {}
        return {
            "NVIDIA_VISIBLE_DEVICES": ",".join(gpus),
            "NVIDIA_DRIVER_CAPABILITIES": NVIDIA_CAPABILITIES,
        }

    @override
    def _runtime_env(self) -> dict[str, str]:
        return {
            # Apptainer reads both prefixes; set the modern one and let the alias inherit.
            "APPTAINER_CACHEDIR": str(self._cache_path),
            "APPTAINER_TMPDIR": str(self._tmp_path()),
            "SINGULARITY_CACHEDIR": str(self._cache_path),
            "SINGULARITY_TMPDIR": str(self._tmp_path()),
        }

    # ------------------------------------------------------------------ images
    def _sandbox(self, image_ref: str) -> Path:
        return self._data_path / f"{_slug(image_ref)}.sbx"

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
        return self._sandbox(image_ref).is_dir()

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
        sandbox = self._sandbox(image_ref)
        # Build beside the live one and swap. `--force` would overwrite in place, which leaves a
        # half-built rootfs behind for image_exists() to report as present if the build dies.
        staging = sandbox.with_name(f".pull-{os.getpid()}-{sandbox.name}")
        try:
            await asyncio.to_thread(shutil.rmtree, staging, ignore_errors=True)
            # `--no-https` is not a fallback, it pins the scheme to http. Passing it for every
            # pull sent public-registry traffic to port 80. Only a registry we already treat as
            # insecure gets it; the same decision the metadata probe makes.
            scheme_args = (
                ["--no-https"] if is_insecure_registry(image_ref, self._registry_hosts_dir) else []
            )
            rc, _out, err = await self._run(
                self._binary,
                "build",
                "--force",
                *scheme_args,
                "--sandbox",
                str(staging),
                f"docker://{image_ref}",
            )
            if rc != 0:
                raise RuntimeError(
                    f"{self._binary} build failed for {image_ref}: {err.decode(errors='replace')}"
                )
            await asyncio.to_thread(shutil.rmtree, sandbox, ignore_errors=True)
            await asyncio.to_thread(os.replace, staging, sandbox)
        finally:
            await asyncio.to_thread(shutil.rmtree, staging, ignore_errors=True)
        # A sandbox directory carries no OCI config, so record the identity scan_images/check_image
        # need from the registry, exactly as the enroot backend does. A failed probe leaves them
        # null (check_image then re-pulls, never blocks).
        meta = await fetch_image_metadata(image_ref, auth, hosts_dir=self._registry_hosts_dir)
        self._meta(image_ref).write_text(
            json.dumps({
                "ref": image_ref,
                "digest": meta.config_digest if meta else None,
                "config_digest": meta.config_digest if meta else None,
                "architecture": meta.architecture if meta else "",
                "labels": dict(meta.labels) if meta else {},
                "entrypoint": meta.entrypoint if meta else None,
                "cmd": meta.cmd if meta else None,
                "env": meta.env if meta else None,
                "working_dir": meta.working_dir if meta else None,
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
        await asyncio.to_thread(shutil.rmtree, self._sandbox(image_ref), ignore_errors=True)
        self._meta(image_ref).unlink(missing_ok=True)

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        meta = self._read_meta(image_ref)
        if not meta:
            return None
        return meta.get("entrypoint") or meta.get("cmd")

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        """The downloadable artifact is a SIF, built from the sandbox on demand.

        The on-disk form is a directory, which is not something the caller can hand around, so the
        single-file form is produced here rather than kept alongside.
        """
        sandbox = self._sandbox(image_ref)
        if not sandbox.is_dir():
            raise FileNotFoundError(f"no local sandbox for {image_ref}")
        rc, _out, err = await self._run(
            self._binary, "build", "--force", str(dest_path), str(sandbox)
        )
        if rc != 0:
            raise RuntimeError(
                f"{self._binary} build (SIF) failed for {image_ref}: {err.decode(errors='replace')}"
            )

    @override
    async def commit_container(
        self,
        container_id: str,
        *,
        base_image_ref: str,
        target_ref: str,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        """Snapshot the container by flattening its overlay onto a copy of the base sandbox.

        There is no `export` here as there is for enroot: the container's state is the base sandbox
        plus its overlay upperdir, so the snapshot is the two merged. `cp -a` of the base then the
        upper over it is the whole operation, and it is what the runtime already guarantees is a
        consistent view — the container is stopped by the time commit runs.
        """
        base = self._sandbox(base_image_ref)
        target = self._sandbox(target_ref)
        upper = self._overlay_dir(container_id) / "upper"
        if not base.is_dir():
            raise RuntimeError(f"no base sandbox for {base_image_ref}")
        await asyncio.to_thread(force_rmtree, target)
        rc, _out, err = await self._run_as_agent("cp", "-a", str(base), str(target))
        if rc != 0:
            raise RuntimeError(f"could not copy the base sandbox: {err.decode(errors='replace')}")
        if upper.is_dir():
            await asyncio.to_thread(self._merge_overlay, upper, target)
        # The committed image must inherit the base's identity, or the manager reads it as "not
        # present locally" and either re-pulls from a registry that has never heard of it or
        # rejects it outright. See the enroot backend for the full story.
        base_meta = self._read_meta(base_image_ref) or {}
        digest = await asyncio.to_thread(self._sandbox_digest, target)
        self._meta(target_ref).write_text(
            json.dumps({
                "ref": target_ref,
                "digest": digest,
                "config_digest": digest,
                "architecture": base_meta.get("architecture") or "",
                "labels": {**(base_meta.get("labels") or {}), **(labels or {})},
                "entrypoint": base_meta.get("entrypoint"),
                "cmd": base_meta.get("cmd"),
                "env": base_meta.get("env"),
                "working_dir": base_meta.get("working_dir"),
            })
        )

    @staticmethod
    def _merge_overlay(upper: Path, target: Path) -> None:
        """Apply the container's overlay upperdir onto a copy of the base rootfs.

        A plain ``cp -a`` of the upperdir is wrong, and wrong in a way that survives all the way
        into the registry: overlayfs records a *deletion* as a character device with rdev 0:0 at
        the deleted path, so copying it verbatim republished `/etc/hostname` as an unopenable
        `c--------- 0,0` node instead of removing it (measured — the bogus node was found inside
        the pushed OCI layer). Two overlay conventions therefore have to be interpreted here:

        * **whiteout** — a char device with rdev 0 means "this path is deleted"; drop it from the
          merged tree rather than copying the marker.
        * **opaque directory** — the ``overlay.opaque`` xattr means the upper directory *replaces*
          the lower one, so the base's contents of that directory must go first.

        The runtime's own bookkeeping xattrs (``*.overlay.origin`` / ``.impure`` / ``.uuid``) are
        stripped: they describe this container's overlay, not the image being published.
        """
        for parent, dirnames, filenames in os.walk(upper):
            src_dir = Path(parent)
            dst_dir = target / src_dir.relative_to(upper)
            if _is_opaque(src_dir) and dst_dir.is_dir():
                force_rmtree(dst_dir)
            dst_dir.mkdir(parents=True, exist_ok=True)
            _clone_metadata(src_dir, dst_dir)
            for name in [*filenames, *dirnames]:
                src, dst = src_dir / name, dst_dir / name
                info = src.lstat()
                if stat.S_ISCHR(info.st_mode) and info.st_rdev == 0:
                    # Whiteout: the base may hold either a file or a whole directory here.
                    if dst.is_dir() and not dst.is_symlink():
                        force_rmtree(dst)
                    else:
                        dst.unlink(missing_ok=True)
                    if name in dirnames:
                        dirnames.remove(name)  # nothing under a whiteout to walk into
                    continue
                if name in dirnames:
                    continue  # os.walk will visit it and create it above
                _copy_entry(src, dst)

    @staticmethod
    def _sandbox_digest(sandbox: Path) -> str | None:
        """``sha256:<hex>`` over the sandbox's shape, the committed image's only stable identity.

        A directory has no single content to digest, and hashing every byte of a multi-GB rootfs
        on the commit path would be minutes of IO. The digest is only ever compared for equality
        against itself, so the (path, size, mtime) triple of every file is enough to be stable
        across reads and different after a change.
        """
        import hashlib

        digest = hashlib.sha256()
        try:
            for path in sorted(sandbox.rglob("*")):
                try:
                    st = path.lstat()
                except OSError:
                    continue
                rel = path.relative_to(sandbox)
                digest.update(f"{rel}\0{st.st_size}\0{int(st.st_mtime)}\0".encode())
        except OSError as e:
            log.warning("[singularity] cannot digest {}: {!r}", sandbox, e)
            return None
        return f"sha256:{digest.hexdigest()}"

    @override
    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        """Publish the sandbox to a registry as an ordinary single-layer image.

        The rootfs is already a directory, so unlike the enroot backend there is nothing to unpack
        first — it goes straight to a gzipped tar. One layer is the honest shape: a sandbox is a
        whole rootfs, not a stack of diffs.
        """
        sandbox = self._sandbox(image_ref)
        if not sandbox.is_dir():
            raise RuntimeError(f"no local image to push for {image_ref}")
        meta = self._read_meta(image_ref) or {}
        workdir = self._state_path / f".push-{_slug(image_ref)}"
        try:
            await asyncio.to_thread(shutil.rmtree, workdir, ignore_errors=True)
            workdir.mkdir(parents=True, exist_ok=True)
            layer_path = workdir / "layer.tar.gz"
            diff_id = await asyncio.to_thread(write_layer, sandbox, layer_path)
            await fetch_push(
                image_ref,
                layer_path=layer_path,
                layer_diff_id=diff_id,
                config=self._image_config(meta),
                auth=auth,
                hosts_dir=self._registry_hosts_dir,
            )
        finally:
            await asyncio.to_thread(shutil.rmtree, workdir, ignore_errors=True)

    @staticmethod
    def _image_config(meta: Mapping[str, Any]) -> dict[str, Any]:
        """The image config document, rebuilt from the sidecar. ``rootfs`` is the pusher's."""
        config: dict[str, Any] = {"Labels": dict(meta.get("labels") or {})}
        if entrypoint := meta.get("entrypoint"):
            config["Entrypoint"] = list(entrypoint)
        if cmd := meta.get("cmd"):
            config["Cmd"] = list(cmd)
        if env := meta.get("env"):
            config["Env"] = list(env)
        if working_dir := meta.get("working_dir"):
            config["WorkingDir"] = str(working_dir)
        return {
            "architecture": meta.get("architecture") or "amd64",
            "os": "linux",
            "config": config,
            "history": [{"created_by": "backend.ai singularity commit"}],
        }

    # ------------------------------------------------------------------ container lifecycle
    def _overlay_dir(self, container_id: str) -> Path:
        return self._runtime_path / container_id

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
        # Creating a container is two mkdirs. The image sandbox stays shared and read-only; every
        # write this container makes lands in `upper/`, so nothing is copied and two kernels of the
        # same image cannot see each other's changes (measured).
        self._specs[container_id] = oci_spec
        self._commands[container_id] = list(command)
        self._images[container_id] = image_ref
        self._labels[container_id] = dict(oci_spec.get("labels") or {})
        self._log_hardening_disposition(container_id, oci_spec)
        if not self._sandbox(image_ref).is_dir():
            raise RuntimeError(f"no local sandbox for {image_ref}")
        overlay = self._overlay_dir(container_id)
        for sub in ("upper", "work"):
            (overlay / sub).mkdir(parents=True, exist_ok=True)
        if os.geteuid() != self._kernel_uid:
            # The runtime runs as the kernel uid, so the overlay it writes through must be its own.
            for path in (overlay, overlay / "upper", overlay / "work"):
                os.chown(path, self._kernel_uid, self._kernel_gid)

    @override
    async def _discard_container(self, container_id: str) -> None:
        # force_rmtree, not shutil.rmtree: overlayfs leaves `work/work` at mode 0000, which plain
        # rmtree cannot descend into — so the overlay, and everything the container wrote into it,
        # would be left on disk for every kernel this node ever runs.
        await asyncio.to_thread(force_rmtree, self._overlay_dir(container_id))

    @override
    def _launch_argv(self, container_id: str, spec: Mapping[str, Any], gate_dir: Path) -> list[str]:
        argv = [
            self._binary,
            "exec",
            # --contain is NOT optional. Without it apptainer binds the host's /dev wholesale, so a
            # CPU-only kernel on a GPU node sees every /dev/nvidia* even with no GPU flag at all
            # (measured). It also gives the container its own /dev/shm and drops the host's home
            # and /tmp, which is the isolation the OCI spec's mounts assume.
            "--contain",
            # A fresh loopback-only netns for the network layer to attach veth to. Unprivileged
            # apptainer allows --net only with --network none, which is exactly what is wanted:
            # the agent (or the privnet) builds the data plane, never the runtime.
            "--net",
            "--network",
            "none",
            # Maps container-root to the invoking (kernel) uid, the scratch owner — apptainer's
            # equivalent of enroot's --root. The kernel-runner then stays root inside and still
            # owns its scratch on the host, with no host privilege.
            "--fakeroot",
            # Its own UTS namespace so the kernel can carry its cluster hostname (create_task sets
            # it once the container is up) and its own PID namespace. apptainer puts `appinit` at
            # PID 1 there, so zombies are reaped — something enroot does not provide.
            "--uts",
            "--pid",
            # And its own SysV IPC namespace. `--contain` does NOT cover this, whatever its name
            # suggests: measured, apptainer's own `appinit` — PID 1 in the container — sat in the
            # HOST's IPC namespace and listed every host segment, while the workload below it was
            # isolated by the gate wrapper's unshare. Passing this moves PID 1 itself, so the
            # container has no process left in the host's namespace. Unlike enroot, apptainer has
            # no /dev-rebuilding hook to trip over here, so it simply works.
            "--ipc",
            # Start from an empty environment; everything the kernel needs is passed explicitly
            # below. Without this the agent pod's own environment (NVIDIA_VISIBLE_DEVICES=all, to
            # get the driver injected into the *pod*) would reach the container.
            "--cleanenv",
            # The per-container writable layer. The image sandbox is never modified.
            "--overlay",
            str(self._overlay_dir(container_id)),
            "--bind",
            f"{gate_dir}:{GATE_MNT}:rw",
        ]
        # Host binds from the OCI spec (scratch config/work, krunner, vfolders, /etc/hosts, ...).
        # apptainer creates a missing mountpoint itself, so the spec's targets need not pre-exist.
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
            # Both spellings of read-only reach here; dropping either would hand the kernel a
            # writable krunner and writable read-only vfolders.
            mode = "ro" if mount.get("readonly") or "ro" in opts else "rw"
            argv += ["--bind", f"{src}:{dst}:{mode}"]
        # /dev node passthrough (AMD ROCm, NPUs, InfiniBand HCAs). --contain gives a minimal /dev,
        # so anything an accelerator plugin asked for has to be bound back in explicitly.
        for device in spec.get("devices", []):
            src, dst = device.get("source"), device.get("destination") or device.get("source")
            if not src:
                continue
            argv += ["--bind", f"{src}:{dst}:rw"]
        gpus = [str(g) for g in (spec.get("gpus") or [])]
        if gpus:
            # --nvccli drives the same nvidia-container-cli the enroot backend's hook uses, so the
            # allocation is enforced by device injection rather than advertised by an environment
            # variable. The alternative, --nv, IGNORES NVIDIA_VISIBLE_DEVICES entirely and injects
            # every device on the node (measured) — unusable where kernels share a node.
            argv.append("--nvccli")
        env = {str(k): str(v) for k, v in (spec.get("env") or {}).items()}
        if gpus:
            env["NVIDIA_VISIBLE_DEVICES"] = ",".join(gpus)
            env.setdefault("NVIDIA_DRIVER_CAPABILITIES", NVIDIA_CAPABILITIES)
        else:
            # No sentinel: apptainer rejects enroot's `void`/`none` outright ("unknown device"), so
            # "no GPU" is expressed by omitting --nvccli above. Drop the variable so nothing
            # downstream reads a stale allocation out of it.
            env.pop("NVIDIA_VISIBLE_DEVICES", None)
        # The kernel-runner must stay container-root, which --fakeroot maps to the host kernel uid
        # (the scratch owner). A non-zero LOCAL_USER_ID would be an unmapped uid in the rootless
        # userns (-> nobody) and could not read the scratch it owns on the host.
        env["LOCAL_USER_ID"] = "0"
        env["LOCAL_GROUP_ID"] = "0"
        for key, value in env.items():
            if "\n" in value:
                # A newline would split one variable into two on apptainer's side. The runner still
                # sees the value via /home/config/environ.txt.
                log.warning(
                    "[singularity] dropping multi-line env var {} from the container env", key
                )
                continue
            argv += ["--env", f"{key}={value}"]
        # The image sandbox, then the pause-wrapper as the command with the real command as its
        # args — the two-phase gate the network layer attaches inside.
        argv += [
            str(self._sandbox(self._images[container_id])),
            f"{GATE_MNT}/pause.sh",
            *self._commands.get(container_id, ()),
        ]
        return argv
