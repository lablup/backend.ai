import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self, override

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.bgtask.task.base import BaseBackgroundTaskArgs, BaseBackgroundTaskHandler
from ai.backend.common.bgtask.types import TaskName
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.vfolder.anycast import (
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.types import DispatchResult, VFolderID
from ai.backend.logging import BraceStyleAdapter

from ...volumes.pool import VolumePool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class VFolderDeleteTaskArgs(BaseBackgroundTaskArgs):
    volume: str
    vfolder_id: VFolderID

    @override
    def to_metadata_body(self) -> dict[str, Any]:
        return {
            "volume": self.volume,
            "vfolder_id": str(self.vfolder_id),
        }

    @classmethod
    @override
    def from_metadata_body(cls, body: Mapping[str, Any]) -> Self:
        return cls(
            volume=body["volume"],
            vfolder_id=VFolderID.from_str(body["vfolder_id"]),
        )


class VFolderDeleteTaskHandler(BaseBackgroundTaskHandler[VFolderDeleteTaskArgs]):
    _volume_pool: VolumePool
    _event_producer: EventProducer

    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    @classmethod
    @override
    def name(cls) -> TaskName:
        return TaskName.DELETE_VFOLDER

    @override
    async def execute(
        self, reporter: ProgressReporter, args: VFolderDeleteTaskArgs
    ) -> DispatchResult:
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
            return DispatchResult(errors=[str(e)])
        else:
            await self._event_producer.anycast_event(
                VFolderDeletionSuccessEvent(
                    args.vfolder_id,
                )
            )
        return DispatchResult()

    @classmethod
    @override
    def args_type(cls) -> type[VFolderDeleteTaskArgs]:
        return VFolderDeleteTaskArgs
