import asyncio
from pathlib import Path
from typing import AsyncIterator, Mapping, Protocol, Dict, Any
import weakref

from ai.backend.common.events import DoVolumeMountEvent, DoVolumeUnmountEvent
from ai.backend.common.types import VFolderID
from ai.backend.storage.abc import AbstractVolume
from ai.backend.storage.api.vfolder.types import VFolderData, VolumeBaseData
from ai.backend.storage.context import RootContext
from ai.backend.storage.types import VolumeInfo


class VFolderServiceProtocol(Protocol):
    async def get_volume(self, volume_data: VolumeBaseData) -> AsyncIterator[AbstractVolume]:
        """by volume_id"""
        ...

    async def get_volumes(self) -> Mapping[str, VolumeInfo]:
        ...

    async def create_vfolder(self, volume_id: str, vfolder_id: VFolderID, options: VFolderOptions) -> None:
        ...

    async def clone_vfolder(self, volume_id: str, vfolder_id: VFolderID, new_vfolder_id: VFolderID, options: VFolderOptions) -> None:
        ...

    async def get_vfolders(self, volume_id: str) -> list[Dict[str, Any]]:
        ...

    async def get_vfolder_info(self, volume_id: str, vfolder_id: VFolderID) -> Dict[str, Any]:
        ...

    """TODO: options type 정의 필요
    create 시와 필드가 겹친다면 따로 정의 X"""

    async def update_vfolder_options(self, volume_id: str, vfolder_id: VFolderID, options: ...) -> None:
        ...

    async def delete_vfolder(self, volume_id: str, vfolder_id: VFolderID) -> None:
        ...


class VFolderService(VFolderServiceProtocol):
    def __init__(self, ctx: RootContext) -> None:
        self.ctx = ctx

    async def get_volume(self, volume_data: VolumeBaseData) -> AsyncIterator[AbstractVolume]:
        ...

    async def get_volumes(self) -> Mapping[str, VolumeInfo]:
        ...

    async def handle_volume_mount(self, event: DoVolumeMountEvent) -> None:
        ...

    async def handle_volume_umount(self, event: DoVolumeUnmountEvent) -> None:
        ...

    async def create_vfolder(self, vfolder_data: VFolderData) -> None:
        ...

    async def clone_vfolder(self, vfolder_data: VFolderData, new_vfolder_id: VFolderID) -> None:
        ...

    async def get_vfolders(self, volume_id: str) -> list[Dict[str, Any]]:
        ...

    async def get_vfolder_info(self, volume_id: str, vfolder_id: VFolderID) -> Dict[str, Any]:
        ...

    async def update_vfolder_options(self, volume_id: str, vfolder_id: VFolderID, options: ...) -> None:
        ...

    async def _delete_vfolder(
        self,
        vfolder_data: VFolderData,
        task_map: weakref.WeakValueDictionary[VFolderID, asyncio.Task]
    ) -> None:
        ...

    async def delete_vfolder(self, vfolder_data: VFolderData) -> None:
        ...
