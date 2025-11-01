from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskArgs,
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskResult,
    EmptyTaskResult,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.vfolder.anycast import (
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.types import VFolderID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.bgtask.types import StorageBgtaskName

if TYPE_CHECKING:
    from ...volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderDeleteTaskArgs(BaseBackgroundTaskArgs):
    volume: str
    vfolder_id: VFolderID


class VFolderDeleteTaskHandler(BaseBackgroundTaskHandler[VFolderDeleteTaskArgs]):
    _volume_pool: VolumePool
    _event_producer: EventProducer

    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    @classmethod
    @override
    def name(cls) -> StorageBgtaskName:
        return StorageBgtaskName.DELETE_VFOLDER  # type: ignore[return-value]

    @override
    async def execute(self, args: VFolderDeleteTaskArgs) -> BaseBackgroundTaskResult:
        try:
            async with self._volume_pool.get_volume_by_name(args.volume) as volume:
                await volume.delete_vfolder(args.vfolder_id)
        except Exception as e:
            log.exception(
                "Failed to delete vfolder (volume=%s, vfolder=%s): %s",
                args.volume,
                args.vfolder_id,
                e,
            )
            await self._event_producer.anycast_event(
                VFolderDeletionFailureEvent(
                    args.vfolder_id,
                    str(e),
                )
            )
            raise e
        else:
            await self._event_producer.anycast_event(
                VFolderDeletionSuccessEvent(
                    args.vfolder_id,
                )
            )
        return EmptyTaskResult()

    @classmethod
    @override
    def args_type(cls) -> type[VFolderDeleteTaskArgs]:
        return VFolderDeleteTaskArgs
