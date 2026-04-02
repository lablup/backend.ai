import asyncio
import logging
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import override

from ai.backend.agent.resources import Mount
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import (
    KernelId,
    MountPermission,
    MountTypes,
    VFolderMount,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class OverlayMountSpec:
    overlay_mounts: list[VFolderMount]
    scratch_root: Path
    kernel_id: KernelId


class OverlayMountSpecGenerator(ArgsSpecGenerator[OverlayMountSpec]):
    pass


@dataclass
class OverlayMountResult:
    mounts: list[Mount]
    merged_paths: list[Path] = field(default_factory=list)


class OverlayMountProvisioner(Provisioner[OverlayMountSpec, OverlayMountResult]):
    """Provisions overlayfs mounts for vfolders with overlay_target set.

    On Linux: creates overlayfs (lower=vfolder ro, upper=overlay_target or temp dir)
    and bind-mounts the merged directory into the container.

    On macOS: falls back to read-only bind mount (overlay not supported).
    """

    @property
    @override
    def name(self) -> str:
        return "docker-overlay-mount"

    @override
    async def setup(self, spec: OverlayMountSpec) -> OverlayMountResult:
        if not spec.overlay_mounts:
            return OverlayMountResult(mounts=[])

        if not sys.platform.startswith("linux"):
            return self._fallback_bind_ro(spec)

        mounts: list[Mount] = []
        merged_paths: list[Path] = []

        for vfmount in spec.overlay_mounts:
            lower = Path(vfmount.host_path)
            overlay_base = spec.scratch_root / str(spec.kernel_id) / "overlay" / vfmount.name

            if vfmount.overlay_target and vfmount.overlay_target.host_path:
                upper = Path(vfmount.overlay_target.host_path)
            else:
                upper = overlay_base / "upper"
                upper.mkdir(parents=True, exist_ok=True)

            work = overlay_base / "work"
            work.mkdir(parents=True, exist_ok=True)
            merged = overlay_base / "merged"
            merged.mkdir(parents=True, exist_ok=True)

            proc = await asyncio.create_subprocess_exec(
                "mount",
                "-t",
                "overlay",
                "overlay",
                "-o",
                f"lowerdir={lower},upperdir={upper},workdir={work}",
                str(merged),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                log.warning(
                    "Failed to create overlay mount for {}: {} (falling back to bind ro)",
                    vfmount.name,
                    stderr.decode().strip(),
                )
                mounts.append(
                    Mount(
                        MountTypes.BIND,
                        lower,
                        Path(vfmount.kernel_path),
                        MountPermission.READ_ONLY,
                    )
                )
                continue

            merged_paths.append(merged)
            mounts.append(
                Mount(
                    MountTypes.BIND,
                    merged,
                    Path(vfmount.kernel_path),
                    MountPermission.READ_WRITE,
                )
            )

        return OverlayMountResult(mounts=mounts, merged_paths=merged_paths)

    @override
    async def teardown(self, resource: OverlayMountResult) -> None:
        for merged in resource.merged_paths:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "umount",
                    str(merged),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            except Exception:
                log.warning("Failed to umount overlay at {}", merged)
            try:
                overlay_base = merged.parent
                shutil.rmtree(overlay_base, ignore_errors=True)
            except Exception:
                log.warning("Failed to cleanup overlay dir at {}", merged.parent)

    def _fallback_bind_ro(self, spec: OverlayMountSpec) -> OverlayMountResult:
        log.warning("Overlay mount not supported on this platform, falling back to bind ro")
        mounts = [
            Mount(
                MountTypes.BIND,
                Path(vfmount.host_path),
                Path(vfmount.kernel_path),
                MountPermission.READ_ONLY,
            )
            for vfmount in spec.overlay_mounts
        ]
        return OverlayMountResult(mounts=mounts)


class OverlayMountStage(ProvisionStage[OverlayMountSpec, OverlayMountResult]):
    pass
