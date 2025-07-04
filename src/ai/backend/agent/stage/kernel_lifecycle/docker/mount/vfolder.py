from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, override

from ai.backend.agent.resources import Mount
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import (
    MountTypes,
    VFolderMount,
)


@dataclass
class VFolderMountSpec:
    mounts: list[VFolderMount]
    prevent_vfolder_mounts: bool


class VFolderMountSpecGenerator(SpecGenerator[VFolderMountSpec]):
    def __init__(self, raw_mounts: list[Mapping[str, Any]], prevent_vfolder_mounts: bool) -> None:
        self._raw_mounts = raw_mounts
        self._prevent_vfolder_mounts = prevent_vfolder_mounts

    @override
    async def wait_for_spec(self) -> VFolderMountSpec:
        """
        Waits for the spec to be ready.
        """
        vfolder_mounts = [VFolderMount.from_json(item) for item in self._raw_mounts]
        return VFolderMountSpec(
            mounts=vfolder_mounts, prevent_vfolder_mounts=self._prevent_vfolder_mounts
        )


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
            if spec.prevent_vfolder_mounts:
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
