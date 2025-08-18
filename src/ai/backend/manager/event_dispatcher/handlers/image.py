import logging
from datetime import datetime

from ai.backend.common.events.event_types.image.anycast import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator

from ...models.utils import (
    ExtendedAsyncSAEngine,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageEventHandler:
    def __init__(
        self,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        use_sokovan: bool,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        self._registry = registry
        self._db = db
        self._use_sokovan = use_sokovan
        self._schedule_coordinator = schedule_coordinator

    async def handle_image_pull_started(
        self,
        context: None,
        agent_id: AgentId,
        ev: ImagePullStartedEvent,
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp)
        log.debug("handle_image_pull_started: ag:{} img:{}, start_dt:{}", ev.agent_id, ev.image, dt)

        if self._use_sokovan:
            # Use new Sokovan logic for kernel state management
            await self._schedule_coordinator.update_kernels_to_pulling_for_image(
                ev.agent_id, ev.image, ev.image_ref.canonical if ev.image_ref else None
            )
        else:
            # Use legacy registry logic
            async with self._db.connect() as db_conn:
                await self._registry.mark_image_pull_started(
                    ev.agent_id, ev.image, ev.image_ref, db_conn=db_conn
                )

    async def handle_image_pull_finished(
        self, context: None, agent_id: AgentId, ev: ImagePullFinishedEvent
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp)
        log.debug("handle_image_pull_finished: ag:{} img:{}, end_dt:{}", ev.agent_id, ev.image, dt)

        if self._use_sokovan:
            # Use new Sokovan logic for kernel state management
            await self._schedule_coordinator.update_kernels_to_prepared_for_image(
                ev.agent_id, ev.image, ev.image_ref.canonical if ev.image_ref else None
            )
        else:
            # Use legacy registry logic
            async with self._db.connect() as db_conn:
                await self._registry.mark_image_pull_finished(
                    ev.agent_id, ev.image, ev.image_ref, db_conn=db_conn
                )

    async def handle_image_pull_failed(
        self,
        context: None,
        agent_id: AgentId,
        ev: ImagePullFailedEvent,
    ) -> None:
        log.warning("handle_image_pull_failed: ag:{} img:{}, msg:{}", ev.agent_id, ev.image, ev.msg)

        if self._use_sokovan:
            # Use new Sokovan logic for kernel state management
            await self._schedule_coordinator.cancel_kernels_for_failed_image(
                ev.agent_id, ev.image, ev.msg, ev.image_ref.canonical if ev.image_ref else None
            )
        else:
            # Use legacy registry logic
            async with self._db.connect() as db_conn:
                await self._registry.handle_image_pull_failed(
                    ev.agent_id, ev.image, ev.msg, ev.image_ref, db_conn=db_conn
                )
