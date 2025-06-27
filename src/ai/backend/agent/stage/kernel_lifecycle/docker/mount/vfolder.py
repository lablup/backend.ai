import sys
import asyncio
from dataclasses import dataclass
from typing import override, Any
from decimal import Decimal
from pathlib import Path
from collections.abc import Mapping
from functools import partial
import secrets
import itertools

from aiodocker.docker import Docker
import aiotools

from ai.backend.agent.proxy import DomainSocketProxy, proxy_connection
from ai.backend.agent.types import VolumeInfo
from ai.backend.agent.exception import UnsupportedResource
from ai.backend.agent.resources import known_slot_types, KernelResourceSpec,Mount, allocate
from ai.backend.common.asyncio import closing_async
from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import (
    ResourceSlot,
    MountTypes,
    MountPermission,
    SlotName,
    current_resource_slots,
    VFolderMount,
)


@dataclass
class VFolderMountSpec:
    mounts: list[VFolderMount]
    internal_data: Mapping[str, Any]


class VFolderMountSpecGenerator(SpecGenerator[VFolderMountSpec]):
    def __init__(self, raw_mounts: list[Mapping[str, Any]]) -> None:
        self._raw_mounts = raw_mounts
    
    @override
    async def wait_for_spec(self) -> VFolderMountSpec:
        """
        Waits for the spec to be ready.
        """
        vfolder_mounts= [VFolderMount.from_json(item) for item in self._raw_mounts]
        return VFolderMountSpec(mounts=vfolder_mounts)


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
            if spec.internal_data.get("prevent_vfolder_mounts", False):
                if vfolder.name != ".logs":
                    continue
            mount = Mount(
                MountTypes.BIND,
                Path(vfolder.host_path),
                Path(vfolder.kernel_path),
                vfolder.mount_perm,
            )
            result.append(mount)
        return VFolderMountResult(
            mounts=result
        )


    @override
    async def teardown(self, resource: None) -> None:
        pass


class VFolderMountStage(ProvisionStage[VFolderMountSpec, VFolderMountResult]):
    pass
