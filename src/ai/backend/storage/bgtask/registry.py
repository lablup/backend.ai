from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.dispatcher import EventProducer

from ..volumes.pool import VolumePool
from .tasks.clone import VFolderCloneTaskHandler
from .tasks.delete import VFolderDeleteTaskHandler


class BgtaskHandlerRegistryCreator:
    def __init__(
        self,
        volume_pool: VolumePool,
        event_producer: EventProducer,
        bgtask_client: ValkeyBgtaskClient,
    ) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer
        self._bgtask_client = bgtask_client

    def create(self) -> BackgroundTaskHandlerRegistry:
        registry = BackgroundTaskHandlerRegistry(self._bgtask_client)

        registry.register_single_task(
            VFolderCloneTaskHandler(self._volume_pool, self._event_producer)
        )
        registry.register_single_task(
            VFolderDeleteTaskHandler(self._volume_pool, self._event_producer)
        )

        return registry
