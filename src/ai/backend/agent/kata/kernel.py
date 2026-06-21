"""
KataKernel — a DockerKernel whose per-container operations are driven through
``nerdctl`` (containerd + Kata runtime) instead of the Docker API.

Almost everything in :class:`DockerKernel` is reused verbatim:

* the ZMQ code-runner contract (:class:`DockerCodeRunner`) — the repl ports are
  published to host ``127.0.0.1`` exactly as in the Docker path, so
  ``create_code_runner`` is inherited unchanged;
* ``interrupt_kernel`` / ``check_status`` / ``start_service`` / ``*_service`` —
  these all go through the ZMQ runner, not the container engine.

Operations that address the container by ID are overridden to call ``nerdctl``
(``get_logs``, ``list_files``). File transfer is routed through the **host-side
scratch dir** (the kernel's ``work`` directory), which is bind-mounted into the
Kata guest as a *read-write virtio-fs share*:

* ``accept_file`` (upload) is **inherited unchanged** from :class:`DockerKernel`
  — it writes host-side into ``scratch-root/<kernel_id>/work`` and the bytes
  appear inside the guest over virtio-fs.
* ``download_file`` / ``download_single`` are overridden to **read host-side**
  from that same scratch dir (the Docker path uses the aiodocker
  ``get_archive`` API, which has no containerd equivalent).

This replaces the earlier exec-channel design (tar over ``nerdctl exec``). Live
validation on ``kata-lab-150`` (2026-06-21) showed the exec channel is the wrong
mechanism: ``tar`` over ``nerdctl exec -i`` *hangs even for small files and
poisons the container's whole exec channel*; ``cat`` over ``exec -i`` truncates
payloads above a few KiB. By contrast the rw virtio-fs share round-trips 1 MiB
binary payloads byte-exact in **both** directions (host↔guest md5 match). The
BA-6541 "upload fails" symptom was specific to the Docker ``cp``/``get_archive``
API path, not the shared mount. ``commit`` is stubbed for the MVP
(image-from-container needs a nerdctl/buildkit path).
"""

from __future__ import annotations

import io
import logging
import os
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, override

from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.kata import nerdctl
from ai.backend.common.asyncio import current_loop
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

#: Mirror of DockerKernel's 1 MiB download cap.
_MAX_DOWNLOAD_BYTES = 1048576

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KataKernel(DockerKernel):
    """A kernel running inside a Kata Containers lightweight VM, managed via nerdctl."""

    @override
    async def get_logs(self) -> dict[str, Any]:
        container_id = self.data["container_id"]
        logs = await nerdctl.nerdctl_logs(container_id)
        return {"logs": logs}

    @override
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        # Confine lookable paths to the home directory (mirrors DockerKernel).
        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot list files outside /home/work")

        code = (
            "import json,os,stat,sys\n"
            "files=[]\n"
            "for f in os.scandir(sys.argv[1]):\n"
            "    s=f.stat(follow_symlinks=False)\n"
            "    files.append({'mode':stat.filemode(s.st_mode),'size':s.st_size,"
            "'ctime':s.st_ctime,'mtime':s.st_mtime,'atime':s.st_atime,'filename':f.name})\n"
            "print(json.dumps(files))\n"
        )
        _rc, raw_out, raw_err = await nerdctl.nerdctl_exec(
            self.data["container_id"],
            [
                "/opt/backend.ai/bin/python",
                "-c",
                code,
                str(container_abspath),
            ],
        )
        return {
            "files": raw_out.decode("utf-8"),
            "errors": raw_err.decode("utf-8"),
            "abspath": str(container_path),
        }

    def _resolve_host_work_path(self, container_path: os.PathLike[str] | str) -> Path:
        """
        Map a container-relative path under ``/home/work`` to its host-side
        location in the scratch dir (the rw virtio-fs share), with the same
        path-escape guard DockerKernel applies. ``accept_file`` (inherited) and
        the download overrides both go through this single host-side view.
        """
        host_work_dir: Path = (
            self.agent_config["container"]["scratch-root"] / str(self.kernel_id) / "work"
        )
        host_abspath = (host_work_dir / container_path).resolve(strict=False)
        if not host_abspath.is_relative_to(host_work_dir):
            raise PermissionError("You cannot access files outside /home/work")
        return host_abspath

    # accept_file (upload) is inherited from DockerKernel: a host-side write into
    # scratch-root/<kernel_id>/work, which the guest sees over rw virtio-fs.

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        # Docker returns a tar archive (via get_archive); preserve that contract
        # but build the archive from the host-side scratch file instead.
        loop = current_loop()
        host_abspath = self._resolve_host_work_path(container_path)

        def _read_as_tar() -> bytes:
            if host_abspath.stat().st_size > _MAX_DOWNLOAD_BYTES:
                raise ValueError("Too large archive file exceeding 1 MiB")
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w") as tf:
                tf.add(str(host_abspath), arcname=host_abspath.name)
            return buf.getvalue()

        return await loop.run_in_executor(None, _read_as_tar)

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        loop = current_loop()
        host_abspath = self._resolve_host_work_path(container_path)

        def _read_bytes() -> bytes:
            if host_abspath.stat().st_size > _MAX_DOWNLOAD_BYTES:
                raise ValueError("Too large archive file exceeding 1 MiB")
            return host_abspath.read_bytes()

        return await loop.run_in_executor(None, _read_bytes)

    @override
    async def commit(
        self,
        kernel_id: KernelId,
        subdir: str,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] | None = None,
    ) -> None:
        # MVP degradation: image-from-container (commit) is not implemented for the
        # Kata/nerdctl path. Production would shell out to `nerdctl commit` +
        # `nerdctl save`, or use a buildkit export. See findings report.
        raise NotImplementedError(
            "commit (image-from-container) is not supported by the KataAgent MVP"
        )
