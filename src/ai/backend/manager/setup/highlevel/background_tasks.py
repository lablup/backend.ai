from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.metrics.metric import BgTaskMetricObserver
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.setup.messaging.event_producer import EventProducerResource


@dataclass
class BackgroundTaskManagerSpec:
    event_producer_resource: EventProducerResource
    bgtask_observer: BgTaskMetricObserver


class BackgroundTaskManagerProvisioner(Provisioner[BackgroundTaskManagerSpec, BackgroundTaskManager]):
    @property
    def name(self) -> str:
        return "background_task_manager"

    async def setup(self, spec: BackgroundTaskManagerSpec) -> BackgroundTaskManager:
        background_task_manager = BackgroundTaskManager(
            spec.event_producer_resource.event_producer,
            bgtask_observer=spec.bgtask_observer,
        )
        return background_task_manager

    async def teardown(self, resource: BackgroundTaskManager) -> None:
        await resource.shutdown()