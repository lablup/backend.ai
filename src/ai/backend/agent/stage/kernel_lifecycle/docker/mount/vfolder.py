from dataclasses import dataclass
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


class VFolderMountProvisioner(Provisioner[VFolderMountSpec, VFolderMountResult]):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "docker-vfolder-mount"

    @override
    async def setup(self, spec: VFolderMountSpec) -> VFolderMountResult:
        result: list[Mount] = []
        for vfolder in spec.mounts:
            if spec.prevent_vfolder_mount:
                if vfolder.name != ".logs":
                    continue
            mount = Mount(
                MountTypes.BIND,
                Path(vfolder.host_path),
                Path(vfolder.kernel_path),
                vfolder.mount_perm,
            )
            result.append(mount)
        return VFolderMountResult(mounts=result)

    @override
    async def teardown(self, resource: VFolderMountResult) -> None:
        pass


class VFolderMountStage(ProvisionStage[VFolderMountSpec, VFolderMountResult]):
    pass
