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
(``get_logs``, ``list_files``). File transfer (``accept_file`` upload and
``download_*``) is routed through the kernel **exec channel** (tar over
``nerdctl exec``) rather than host-side scratch writes / ``docker get_archive``,
because the host↔guest virtio-fs propagation for those was observed to fail on
Kata (BA-6541), while the exec channel works. ``commit`` is stubbed for the MVP
(image-from-container needs a nerdctl/buildkit path).
"""

from __future__ import annotations

import io
import logging
import os
import tarfile
from pathlib import PurePosixPath
from typing import Any, override

from ai.backend.agent.docker.kernel import DockerKernel
from ai.backend.agent.errors.kata import NerdctlError
from ai.backend.agent.kata import nerdctl
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

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

    async def _download_archive(self, container_abspath: PurePosixPath) -> bytes:
        # Stream a tar archive of the target out of the guest via `nerdctl exec tar`.
        container_id = self.data["container_id"]
        parent = str(container_abspath.parent)
        name = container_abspath.name
        rc, raw_out, raw_err = await nerdctl.nerdctl_exec(
            container_id,
            ["tar", "cf", "-", "-C", parent, name],
            timeout_sec=120.0,
        )
        if rc != 0:
            raise NerdctlError(
                f"could not download {container_abspath} from kata container "
                f"(rc={rc}): {raw_err.decode(errors='replace').strip()}"
            )
        if len(raw_out) > 1048576:
            raise ValueError("Too large archive file exceeding 1 MiB")
        return raw_out

    @override
    async def accept_file(self, container_path: os.PathLike[str] | str, filedata: bytes) -> None:
        # DockerKernel.accept_file writes host-side into the scratch `work` dir and
        # relies on it being visible inside the container. On Kata that host->guest
        # propagation across the virtio-fs boundary is unreliable (observed:
        # in-session file creation works but host-driven upload fails, BA-6541).
        # Stream the file into the guest through the proven exec channel instead.
        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("Not allowed to upload files outside /home/work")
        arcname = str(container_abspath.relative_to(container_home_path))

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            info = tarfile.TarInfo(name=arcname)
            info.size = len(filedata)
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(filedata))
        tar_bytes = buf.getvalue()

        rc, _raw_out, raw_err = await nerdctl.nerdctl_exec(
            self.data["container_id"],
            ["tar", "xf", "-", "-C", str(container_home_path)],
            input_bytes=tar_bytes,
            timeout_sec=120.0,
        )
        if rc != 0:
            raise NerdctlError(
                f"could not upload {container_abspath} into kata container "
                f"(rc={rc}): {raw_err.decode(errors='replace').strip()}"
            )

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot download files outside /home/work")
        return await self._download_archive(container_abspath)

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot download files outside /home/work")
        tar_bytes = await self._download_archive(container_abspath)
        with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tf:
            members = tf.getmembers()
            files = [m for m in members if m.isfile()]
            if len(files) != 1:
                raise ValueError(
                    f"Expected a single-file archive but found {len(files)} files "
                    f"from {container_abspath}"
                )
            extracted = tf.extractfile(files[0])
            if extracted is None:
                raise ValueError(f"Could not read {files[0].name!r} from {container_abspath}")
            return extracted.read()

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
