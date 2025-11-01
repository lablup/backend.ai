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
    VFolderCloneFailureEvent,
    VFolderCloneSuccessEvent,
)
from ai.backend.common.types import VFolderID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.bgtask.types import StorageBgtaskName

if TYPE_CHECKING:
    from ...volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderCloneTaskArgs(BaseBackgroundTaskArgs):
    volume: str
    src_vfolder: VFolderID
    dst_vfolder: VFolderID


class VFolderCloneTaskHandler(BaseBackgroundTaskHandler[VFolderCloneTaskArgs]):
    _volume_pool: VolumePool
    _event_producer: EventProducer

    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    @classmethod
    @override
    def name(cls) -> StorageBgtaskName:
        return StorageBgtaskName.CLONE_VFOLDER  # type: ignore[return-value]

    @classmethod
    @override
    def args_type(cls) -> type[VFolderCloneTaskArgs]:
        return VFolderCloneTaskArgs

    @override
    async def execute(self, args: VFolderCloneTaskArgs) -> BaseBackgroundTaskResult:
        try:
            async with self._volume_pool.get_volume_by_name(args.volume) as volume:
                await volume.clone_vfolder(
                    args.src_vfolder,
                    args.dst_vfolder,
                )
        except Exception as e:
            log.exception(
                f"VFolder cloning task failed. (src_vfid:{args.src_vfolder}, dst_vfid:{args.dst_vfolder}, e:{str(e)})"
            )
            await self._event_producer.anycast_event(
                VFolderCloneFailureEvent(
                    args.src_vfolder,
                    args.dst_vfolder,
                    str(e),
                )
            )
            raise e
        else:
            await self._event_producer.anycast_event(
                VFolderCloneSuccessEvent(
                    args.src_vfolder,
                    args.dst_vfolder,
                )
            )
        return EmptyTaskResult()
