from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.events.dispatcher import EventProducer

from ..volumes.pool import VolumePool
from .tasks.clone import VFolderCloneTaskHandler
from .tasks.delete import VFolderDeleteTaskHandler


class BgtaskHandlerRegistryCreator:
    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    def create(self) -> BackgroundTaskHandlerRegistry:
        registry = BackgroundTaskHandlerRegistry()
        registry.register(VFolderCloneTaskHandler(self._volume_pool, self._event_producer))
        registry.register(VFolderDeleteTaskHandler(self._volume_pool, self._event_producer))

        return registry
