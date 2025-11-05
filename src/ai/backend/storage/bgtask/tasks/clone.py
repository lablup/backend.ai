from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from pydantic import Field

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.vfolder.anycast import (
    VFolderCloneFailureEvent,
    VFolderCloneSuccessEvent,
)
from ai.backend.common.type_adapters import VFolderIDField
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.bgtask.types import StorageBgtaskName

if TYPE_CHECKING:
    from ...volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderCloneManifest(BaseBackgroundTaskManifest):
    """
    Manifest for cloning a virtual folder.
    """

    volume: str = Field(description="Volume name where the vfolders are located")
    src_vfolder: VFolderIDField = Field(description="Source vfolder ID to clone from")
    dst_vfolder: VFolderIDField = Field(description="Destination vfolder ID to clone to")


class VFolderCloneTaskHandler(BaseBackgroundTaskHandler[VFolderCloneManifest, None]):
    _volume_pool: VolumePool
    _event_producer: EventProducer

    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    @classmethod
    @override
    def name(cls) -> StorageBgtaskName:
        return StorageBgtaskName.CLONE_VFOLDER

    @classmethod
    @override
    def manifest_type(cls) -> type[VFolderCloneManifest]:
        return VFolderCloneManifest

    @override
    async def execute(self, manifest: VFolderCloneManifest) -> None:
        try:
            async with self._volume_pool.get_volume_by_name(manifest.volume) as volume:
                await volume.clone_vfolder(
                    manifest.src_vfolder,
                    manifest.dst_vfolder,
                )
        except Exception as e:
            log.exception(
                f"VFolder cloning task failed. (src_vfid:{manifest.src_vfolder}, dst_vfid:{manifest.dst_vfolder}, e:{str(e)})"
            )
            await self._event_producer.anycast_event(
                VFolderCloneFailureEvent(
                    manifest.src_vfolder,
                    manifest.dst_vfolder,
                    str(e),
                )
            )
            raise e
        else:
            await self._event_producer.anycast_event(
                VFolderCloneSuccessEvent(
                    manifest.src_vfolder,
                    manifest.dst_vfolder,
                )
            )
