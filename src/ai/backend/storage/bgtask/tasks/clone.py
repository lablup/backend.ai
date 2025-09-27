import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self, override

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskArgs,
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskResult,
    EmptyTaskResult,
)
from ai.backend.common.bgtask.types import TaskName
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.vfolder.anycast import (
    VFolderCloneFailureEvent,
    VFolderCloneSuccessEvent,
)
from ai.backend.common.types import VFolderID
from ai.backend.logging import BraceStyleAdapter

from ...volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class VFolderCloneTaskArgs(BaseBackgroundTaskArgs):
    volume: str
    src_vfolder: VFolderID
    dst_vfolder: VFolderID

    @override
    def to_redis_json(self) -> Mapping[str, Any]:
        return {
            "volume": self.volume,
            "src_vfolder": str(self.src_vfolder),
            "dst_vfolder": str(self.dst_vfolder),
        }

    @classmethod
    @override
    def from_redis_json(cls, body: Mapping[str, Any]) -> Self:
        return cls(
            volume=body["volume"],
            src_vfolder=VFolderID.from_str(body["src_vfolder"]),
            dst_vfolder=VFolderID.from_str(body["dst_vfolder"]),
        )


class VFolderCloneTaskHandler(BaseBackgroundTaskHandler[VFolderCloneTaskArgs]):
    _volume_pool: VolumePool
    _event_producer: EventProducer

    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    @classmethod
    @override
    def name(cls) -> TaskName:
        return TaskName.CLONE_VFOLDER

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
