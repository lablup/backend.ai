from dataclasses import dataclass, field
from pathlib import Path
from typing import override

from ai.backend.agent.resources import Mount
from ai.backend.common.stage.types import ArgsSpecGenerator, Provisioner, ProvisionStage
from ai.backend.common.types import (
    MountTypes,
    VFolderMount,
)


@dataclass
class VFolderMountSpec:
    mounts: list[VFolderMount]
    prevent_vfolder_mount: bool


class VFolderMountSpecGenerator(ArgsSpecGenerator[VFolderMountSpec]):
    pass


@dataclass
class VFolderMountResult:
    mounts: list[Mount]
    overlay_mounts: list[VFolderMount] = field(default_factory=list)


class VFolderMountProvisioner(Provisioner[VFolderMountSpec, VFolderMountResult]):
    """Provisioner for regular vfolder bind mounts.

    VFolders with overlay_target set are separated into overlay_mounts
    for the OverlayMountProvisioner to handle.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-vfolder-mount"

    @override
    async def setup(self, spec: VFolderMountSpec) -> VFolderMountResult:
        result: list[Mount] = []
        overlay_mounts: list[VFolderMount] = []
        for vfolder in spec.mounts:
            if spec.prevent_vfolder_mount:
                if vfolder.name != ".logs":
                    continue
            if vfolder.overlay_target is not None:
                overlay_mounts.append(vfolder)
                continue
            mount = Mount(
                MountTypes.BIND,
                Path(vfolder.host_path),
                Path(vfolder.kernel_path),
                vfolder.mount_perm,
            )
            result.append(mount)
        return VFolderMountResult(mounts=result, overlay_mounts=overlay_mounts)

    @override
    async def teardown(self, resource: VFolderMountResult) -> None:
        pass


class VFolderMountStage(ProvisionStage[VFolderMountSpec, VFolderMountResult]):
    pass
