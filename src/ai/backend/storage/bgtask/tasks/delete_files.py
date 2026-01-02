from __future__ import annotations

import logging
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, override

from pydantic import Field

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
)
from ai.backend.common.type_adapters import VFolderIDField
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.bgtask.types import StorageBgtaskName

if TYPE_CHECKING:
    from ...volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class FileDeleteManifest(BaseBackgroundTaskManifest):
    """
    Manifest for deleting files within a virtual folder.
    """

    volume: str = Field(description="Volume name where the vfolder is located")
    vfolder_id: VFolderIDField = Field(description="VFolder ID containing the files")
    relpaths: list[PurePosixPath] = Field(description="Relative paths of files to delete")
    recursive: bool = Field(default=False, description="Whether to delete directories recursively")


class FileDeleteTaskHandler(BaseBackgroundTaskHandler[FileDeleteManifest, None]):
    _volume_pool: VolumePool

    def __init__(self, volume_pool: VolumePool) -> None:
        self._volume_pool = volume_pool

    @classmethod
    @override
    def name(cls) -> StorageBgtaskName:
        return StorageBgtaskName.DELETE_FILES

    @override
    async def execute(self, manifest: FileDeleteManifest) -> None:
        async with self._volume_pool.get_volume_by_name(manifest.volume) as volume:
            await volume.delete_files(
                manifest.vfolder_id,
                manifest.relpaths,
                recursive=manifest.recursive,
            )

    @classmethod
    @override
    def manifest_type(cls) -> type[FileDeleteManifest]:
        return FileDeleteManifest
