"""``EnrootRuntime`` — the **enroot** backend's :class:`~...rootless.base.RootlessOciRuntime`.

Everything a daemonless rootless runtime owes the agent — cgroups, the container journal, log
rotation, death events, the two-phase attachable-netns gate, seccomp — is in the shared base. What
is genuinely enroot's, and so lives here:

* **Images** are ``.sqsh`` squashfs files under ``data_path``. There is no registry client or
  content store, so ``pull_image`` shells out to ``enroot import docker://<ref>`` and a JSON
  **sidecar** (``<slug>.json``) records the identity the OCI model needs — config digest, the
  kernel-spec / base-distro labels, and the base's entrypoint/cmd/env/workdir — because a ``.sqsh``
  cannot be queried for OCI config.
* **The launch line** (``enroot start``), including the GPU allowlist its ``98-nvidia`` hook reads,
  the private ``/dev/shm``, and the host binds carried over from the OCI spec.

**Hardening**: the capability set from the OCI spec is dropped — the userns already scopes caps to
the pod. OCI seccomp is a runc feature, so the base compiles the profile to BPF itself and the
pause wrapper installs it before the user command runs. No MAC profile is applied, which is what
every backend here does (the Docker backend never names one either).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, Final, override

from ai.backend.agent.containerd.runtime.interface import ImageInfo
from ai.backend.agent.rootless.base import (
    DEFAULT_SHM_BYTES,
    GATE_MNT,
    SKIP_MOUNT_TYPES,
    RootlessOciRuntime,
    write_layer,
)
from ai.backend.agent.rootless.registry import fetch_image_metadata, is_insecure_registry
from ai.backend.agent.rootless.registry import push_image as fetch_push
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

_ENROOT_BIN: Final = "enroot"
# enroot slugifies a docker ref into a squashfs filename; we keep the ref in the sidecar and use a
# filesystem-safe slug for the on-disk names so a ref round-trips via the sidecar, not the name.
_SLUG_RE: Final = re.compile(r"[^A-Za-z0-9_.-]+")
_SQSH_DIGEST_CHUNK: Final = 4 * 1024 * 1024


def _slug(image_ref: str) -> str:
    return _SLUG_RE.sub("+", image_ref)


class EnrootRuntime(RootlessOciRuntime):
    backend_name: ClassVar[str] = "enroot"

    @override
    def _runtime_env(self) -> dict[str, str]:
        return {
            "ENROOT_DATA_PATH": str(self._data_path),
            "ENROOT_CACHE_PATH": str(self._cache_path),
            "ENROOT_RUNTIME_PATH": str(self._runtime_path),
        }

    @override
    def _own_existing_artifacts(self) -> None:
        """Hand the enroot artifacts an earlier run left behind to the kernel uid.

        Owning the roots is not enough for a tree that has been used before. An `enroot import`
        run as **root** — which is what this backend did before it went rootless, and what any
        deployment making that switch will have on disk — leaves its layer blobs `root:root 0640`.
        The kernel-uid enroot then finds those layers in cache, cannot read them, and the pull dies
        in the middle with `tar: Cannot open: Permission denied` (measured), which says nothing
        about ownership.

        Only the flat, cheap parts: every cache blob, and the top-level `.sqsh` / `.json` in the
        data path. NOT the container rootfs directories under the data path — those hold tens of
        thousands of files each and are created by the kernel-uid enroot anyway.
        """
        targets = [*self._cache_path.iterdir()]
        targets += [p for p in self._data_path.iterdir() if p.suffix in (".sqsh", ".json")]
        handed_over = 0
        for path in targets:
            try:
                if path.stat().st_uid == self._kernel_uid:
                    continue
                os.chown(path, self._kernel_uid, self._kernel_gid)
                handed_over += 1
            except OSError as e:
                log.warning(
                    "[enroot] cannot hand over {} to uid {}: {!r}", path, self._kernel_uid, e
                )
        if handed_over:
            log.info(
                "[enroot] handed {} pre-existing artifact(s) over to uid {}",
                handed_over,
                self._kernel_uid,
            )

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
        # `enroot import` has no --force and refuses to overwrite, so a re-pull — which is exactly
        # what check_image asks for when the local digest has gone stale — would fail outright on
        # an image the node already has. Import beside it and swap: os.replace is atomic, so a
        # crashed or killed pull also cannot leave a truncated .sqsh behind for image_exists() to
        # report as present.
        staging = sqsh.with_name(f".pull-{os.getpid()}-{sqsh.name}")
        try:
            # `ENROOT_ALLOW_HTTP` does not *permit* http, it FORCES it (enroot 4.2.1
            # `docker.sh`: `if [ -n "$ENROOT_ALLOW_HTTP" ]; then curl_proto="http"`). Setting it
            # for every pull sent public-registry traffic to port 80, where it hung for the full
            # curl timeout. Only a registry we already treat as insecure gets it.
            extra_env = (
                {"ENROOT_ALLOW_HTTP": "y"}
                if is_insecure_registry(image_ref, self._registry_hosts_dir)
                else None
            )
            rc, _out, err = await self._run(
                _ENROOT_BIN,
                "import",
                "-o",
                str(staging),
                f"docker://{image_ref}",
                extra_env=extra_env,
            )
            if rc != 0:
                raise RuntimeError(
                    f"enroot import failed for {image_ref}: {err.decode(errors='replace')}"
                )
            await asyncio.to_thread(os.replace, staging, sqsh)
        finally:
            staging.unlink(missing_ok=True)
        # A `.sqsh` cannot be queried for OCI config, so record the identity scan_images/check_image
        # need — config-blob digest (Docker's `Id`, the manager's image_id) + kernel-spec/base-distro
        # labels + architecture + entrypoint — from the registry. A failed probe leaves them null
        # (check_image then re-pulls, never blocks).
        meta = await fetch_image_metadata(image_ref, auth, hosts_dir=self._registry_hosts_dir)
        self._meta(image_ref).write_text(
            json.dumps({
                "ref": image_ref,
                "digest": meta.config_digest if meta else None,
                "config_digest": meta.config_digest if meta else None,
                "architecture": meta.architecture if meta else "",
                "labels": dict(meta.labels) if meta else {},
                "entrypoint": meta.entrypoint if meta else None,
                # Needed to republish a commit faithfully: an image that loses the base's Cmd,
                # PATH/LANG or working directory is not the same image.
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
        self._sqsh(image_ref).unlink(missing_ok=True)
        self._meta(image_ref).unlink(missing_ok=True)

    @override
    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        """Publish a local `.sqsh` to a registry as an ordinary single-layer image.

        Neither sibling backend does this itself — Docker delegates to dockerd, containerd to its
        Transfer service — but enroot has no daemon to delegate to, and its images are squashfs
        rather than OCI tar layers. So the rootfs is unpacked, retarred as one gzipped layer, and
        uploaded through the registry v2 API (see :mod:`...rootless.registry`). One layer is the
        honest shape: `enroot export` snapshots a whole rootfs, not a stack of diffs.

        Without this the customized-image round trip stops after commit — the image exists on the
        node that made it and can never be scheduled anywhere else.
        """
        sqsh = self._sqsh(image_ref)
        if not sqsh.exists():
            raise RuntimeError(f"no local image to push for {image_ref}")
        meta = self._read_meta(image_ref) or {}
        workdir = self._state_path / f".push-{_slug(image_ref)}"
        try:
            layer_path, diff_id = await self._build_layer(sqsh, workdir)
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
            "history": [{"created_by": "backend.ai enroot commit"}],
        }

    async def _build_layer(self, sqsh: Path, workdir: Path) -> tuple[Path, str]:
        """Unpack the squashfs and retar it as one gzipped layer; return (path, uncompressed digest).

        Run as the agent (not the kernel uid): unsquashfs only restores the recorded ownership when
        it is root, and the recorded ownership is right — `enroot export` remaps the rootless
        container's uids back, so a file the container's root wrote is `root/root` in the `.sqsh`
        even though it is uid 1000 on the host.
        """
        await asyncio.to_thread(shutil.rmtree, workdir, ignore_errors=True)
        rootfs = workdir / "rootfs"
        rootfs.parent.mkdir(parents=True, exist_ok=True)
        rc, _out, err = await self._run_as_agent(
            "unsquashfs", "-no-progress", "-d", str(rootfs), str(sqsh)
        )
        if rc != 0:
            raise RuntimeError(f"unsquashfs failed for {sqsh}: {err.decode(errors='replace')}")
        layer_path = workdir / "layer.tar.gz"
        return layer_path, await asyncio.to_thread(write_layer, rootfs, layer_path)

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        # The downloadable artifact is the squashfs itself for enroot.
        sqsh = self._sqsh(image_ref)
        if not sqsh.exists():
            raise FileNotFoundError(f"no local .sqsh for {image_ref}")
        await asyncio.to_thread(shutil.copyfile, sqsh, dest_path)

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        # What the image runs by default: its Entrypoint, or its Cmd when it has none. (Sidecars
        # written before the two were separated carry the collapsed value under `entrypoint`, so
        # this reads them unchanged.)
        meta = self._read_meta(image_ref)
        if not meta:
            return None
        return meta.get("entrypoint") or meta.get("cmd")

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
            _ENROOT_BIN, "export", "--force", "--output", str(self._sqsh(target_ref)), container_id
        )
        if rc != 0:
            raise RuntimeError(
                f"enroot export failed for {container_id}: {err.decode(errors='replace')}"
            )
        # The committed image needs an identity of its own, and it must inherit the base's.
        # Writing nulls here (the first cut) made `image_config_digest` return None, which
        # check_image reads as "not present locally" — so a just-committed image was either
        # re-pulled from a registry that has never heard of it, or rejected outright as
        # ImageNotAvailable. Dropping the base's labels was just as bad: `ai.backend.kernelspec`
        # and the base-distro label are what the agent needs to launch a kernel from it at all.
        base = self._read_meta(base_image_ref) or {}
        digest = await asyncio.to_thread(self._sqsh_digest, self._sqsh(target_ref))
        self._meta(target_ref).write_text(
            json.dumps({
                "ref": target_ref,
                # A committed image has no registry and so no config blob to be digested. Its
                # content IS the squashfs, so that is what identifies it — stable, and different
                # for every commit, which is all the digest is compared for.
                "digest": digest,
                "config_digest": digest,
                "architecture": base.get("architecture") or "",
                "labels": {**(base.get("labels") or {}), **(labels or {})},
                "entrypoint": base.get("entrypoint"),
                "cmd": base.get("cmd"),
                "env": base.get("env"),
                "working_dir": base.get("working_dir"),
            })
        )

    @staticmethod
    def _sqsh_digest(sqsh: Path) -> str | None:
        """``sha256:<hex>`` over the squashfs, the committed image's only stable identity."""
        digest = hashlib.sha256()
        try:
            with sqsh.open("rb") as f:
                while chunk := f.read(_SQSH_DIGEST_CHUNK):
                    digest.update(chunk)
        except OSError as e:
            log.warning("[enroot] cannot digest {}: {!r}", sqsh, e)
            return None
        return f"sha256:{digest.hexdigest()}"

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
    async def _discard_container(self, container_id: str) -> None:
        await self._run(_ENROOT_BIN, "remove", "--force", container_id)

    @override
    def _launch_argv(self, container_id: str, spec: Mapping[str, Any], gate_dir: Path) -> list[str]:
        # enroot -m FSTAB: `x-create=auto` makes enroot create the mountpoint (file or dir, matching
        # the source) inside the container — the OCI spec's targets do not pre-exist in the image
        # rootfs. `bind` + `ro`/`rw` set the mode.
        argv = [
            _ENROOT_BIN,
            "start",
            # --root remaps container-root to the (kernel-uid) invoker. Combined with running enroot
            # as the kernel uid (see _uid_drop_prefix), the container's root IS the kernel uid on
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
            f"{gate_dir}:{GATE_MNT}:none:x-create=auto,bind,rw",
            # enroot's default fstab BINDS the host's /dev/shm into every container, so all kernels
            # on a node share one /dev/shm — they see each other's segments and compete for its
            # size. Give each its own tmpfs, sized from the session's `shmem` resource_opt (Docker's
            # ShmSize) and defaulting to Docker's 64 MiB. Later -m entries win, so this overrides
            # the fstab bind.
            "-m",
            (
                f"tmpfs:/dev/shm:tmpfs:x-create=dir,rw,nosuid,nodev,mode=1777,"
                f"size={int(spec.get('shmem') or DEFAULT_SHM_BYTES)}"
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
            if mtype in SKIP_MOUNT_TYPES:
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
        argv += [container_id, f"{GATE_MNT}/pause.sh", *self._commands.get(container_id, ())]
        return argv
