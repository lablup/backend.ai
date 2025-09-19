from dataclasses import dataclass

from ai.backend.common.bgtask.bgtask import BackgroundTaskObserver
from ai.backend.common.bgtask.task.executor import (
    BaseBackgroundTaskExecutor,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import (
    BgtaskNotRegisteredError,
)

from ..types import TaskName
from .base import BaseBackgroundTaskHandler


@dataclass
class BackgroundTaskHandlerRegistryArgs:
    valkey_client: ValkeyBgtaskClient
    event_producer: EventProducer
    metric_observer: BackgroundTaskObserver
    server_id: str


class BackgroundTaskHandlerRegistry:
    _registry: dict[TaskName, BaseBackgroundTaskExecutor]
    _valkey_client: ValkeyBgtaskClient
    _event_producer: EventProducer
    _metric_observer: BackgroundTaskObserver
    _server_id: str

    def __init__(self, args: BackgroundTaskHandlerRegistryArgs) -> None:
        self._valkey_client = args.valkey_client
        self._event_producer = args.event_producer
        self._metric_observer = args.metric_observer
        self._server_id = args.server_id
        self._registry = {}

    def register_task(self, handler: BaseBackgroundTaskHandler) -> None:
        executor = BaseBackgroundTaskExecutor(
            handlers=handler,
            valkey_client=self._valkey_client,
            event_producer=self._event_producer,
            metric_observer=self._metric_observer,
            server_id=self._server_id,
        )
        self._registry[handler.name()] = executor

    # def register_batch_task(self, batch_task_name: TaskName, handlers: list[BaseBackgroundTaskHandler]) -> None:
    #     executor = BaseBackgroundTaskExecutor(
    #         handlers=handlers,
    #         valkey_client=self._valkey_client,
    #         event_producer=self._event_producer,
    #         metric_observer=self._metric_observer,
    #         server_id=self._server_id,
    #     )
    #     self._registry[batch_task_name] = executor

    def get_task_executor(self, name: TaskName) -> BaseBackgroundTaskExecutor:
        try:
            return self._registry[name]
        except KeyError:
            raise BgtaskNotRegisteredError
