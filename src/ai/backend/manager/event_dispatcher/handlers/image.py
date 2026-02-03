import logging
from datetime import UTC, datetime

from ai.backend.common.events.event_types.image.anycast import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageEventHandler:
    def __init__(
        self,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        schedule_coordinator: ScheduleCoordinator,
    ) -> None:
        self._registry = registry
        self._db = db
        self._schedule_coordinator = schedule_coordinator

    async def handle_image_pull_started(
        self,
        _context: None,
        _agent_id: AgentId,
        ev: ImagePullStartedEvent,
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp, tz=UTC)
        log.debug("handle_image_pull_started: ag:{} img:{}, start_dt:{}", ev.agent_id, ev.image, dt)

        await self._schedule_coordinator.update_kernels_to_pulling_for_image(
            ev.agent_id, ev.image, ev.image_ref.canonical if ev.image_ref else None
        )

    async def handle_image_pull_finished(
        self, _context: None, _agent_id: AgentId, ev: ImagePullFinishedEvent
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp, tz=UTC)
        log.debug("handle_image_pull_finished: ag:{} img:{}, end_dt:{}", ev.agent_id, ev.image, dt)

        await self._schedule_coordinator.update_kernels_to_prepared_for_image(
            ev.agent_id, ev.image, ev.image_ref.canonical if ev.image_ref else None
        )

    async def handle_image_pull_failed(
        self,
        _context: None,
        _agent_id: AgentId,
        ev: ImagePullFailedEvent,
    ) -> None:
        log.warning("handle_image_pull_failed: ag:{} img:{}, msg:{}", ev.agent_id, ev.image, ev.msg)

        await self._schedule_coordinator.cancel_kernels_for_failed_image(
            ev.agent_id, ev.image, ev.msg, ev.image_ref.canonical if ev.image_ref else None
        )
