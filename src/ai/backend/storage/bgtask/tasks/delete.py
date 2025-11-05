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
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.type_adapters import VFolderIDField
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.bgtask.types import StorageBgtaskName

if TYPE_CHECKING:
    from ...volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderDeleteManifest(BaseBackgroundTaskManifest):
    """
    Manifest for deleting a virtual folder.
    """

    volume: str = Field(description="Volume name where the vfolder is located")
    vfolder_id: VFolderIDField = Field(description="VFolder ID to delete")


class VFolderDeleteTaskHandler(BaseBackgroundTaskHandler[VFolderDeleteManifest, None]):
    _volume_pool: VolumePool
    _event_producer: EventProducer

    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    @classmethod
    @override
    def name(cls) -> StorageBgtaskName:
        return StorageBgtaskName.DELETE_VFOLDER

    @override
    async def execute(self, manifest: VFolderDeleteManifest) -> None:
        try:
            async with self._volume_pool.get_volume_by_name(manifest.volume) as volume:
                await volume.delete_vfolder(manifest.vfolder_id)
        except Exception as e:
            log.exception(
                "Failed to delete vfolder (volume=%s, vfolder=%s): %s",
                manifest.volume,
                manifest.vfolder_id,
                e,
            )
            await self._event_producer.anycast_event(
                VFolderDeletionFailureEvent(
                    manifest.vfolder_id,
                    str(e),
                )
            )
            raise e
        else:
            await self._event_producer.anycast_event(
                VFolderDeletionSuccessEvent(
                    manifest.vfolder_id,
                )
            )

    @classmethod
    @override
    def manifest_type(cls) -> type[VFolderDeleteManifest]:
        return VFolderDeleteManifest
