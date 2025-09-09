from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.events.dispatcher import EventProducer

from ...bgtask.tasks.delete import VFolderDeleteTaskHandler
from ...volumes.pool import VolumePool


class BgtaskHandlerRegistryCreator:
    def __init__(self, volume_pool: VolumePool, event_producer: EventProducer) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer

    def create(self) -> BackgroundTaskHandlerRegistry:
        registry = BackgroundTaskHandlerRegistry()
        registry.register(VFolderDeleteTaskHandler(self._volume_pool, self._event_producer))

        return registry
