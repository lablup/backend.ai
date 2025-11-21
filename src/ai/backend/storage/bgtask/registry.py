from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry

from .tasks.clone import VFolderCloneTaskHandler
from .tasks.delete import VFolderDeleteTaskHandler
from .tasks.delete_files import FileDeleteTaskHandler

if TYPE_CHECKING:
    from ai.backend.common.events.dispatcher import EventProducer

    from ..volumes.pool import VolumePool


class BgtaskHandlerRegistryCreator:
    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    def create(self) -> BackgroundTaskHandlerRegistry:
        registry = BackgroundTaskHandlerRegistry()
        registry.register(VFolderCloneTaskHandler(self._volume_pool, self._event_producer))
        registry.register(VFolderDeleteTaskHandler(self._volume_pool, self._event_producer))
        registry.register(FileDeleteTaskHandler(self._volume_pool))

        return registry
