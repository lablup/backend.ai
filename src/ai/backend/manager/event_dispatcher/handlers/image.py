import logging
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.docker import ImageRef
from ai.backend.common.events.event_types.image.anycast import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.image import ImageRow
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

    async def _resolve_image_id(
        self,
        image: str,
        image_ref: ImageRef | None,
    ) -> UUID | None:
        """Resolve a canonical image string to an image UUID.

        This is the conversion point at the agent boundary where string-based
        image references from agent events are translated to UUID-based references
        used internally by the manager.
        """
        canonical = image_ref.canonical if image_ref else image
        architecture = image_ref.architecture if image_ref else None
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(ImageRow.id).where(ImageRow.name == canonical)
            if architecture:
                query = query.where(ImageRow.architecture == architecture)
            query = query.limit(1)
            result = await db_sess.execute(query)
            return result.scalar_one_or_none()

    async def handle_image_pull_started(
        self,
        _context: None,
        _agent_id: AgentId,
        ev: ImagePullStartedEvent,
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp, tz=UTC)
        log.debug("handle_image_pull_started: ag:{} img:{}, start_dt:{}", ev.agent_id, ev.image, dt)

        image_id = await self._resolve_image_id(ev.image, ev.image_ref)
        await self._schedule_coordinator.update_kernels_to_pulling_for_image(
            ev.agent_id,
            ev.image,
            ev.image_ref.canonical if ev.image_ref else None,
            image_id=image_id,
        )

    async def handle_image_pull_finished(
        self, _context: None, _agent_id: AgentId, ev: ImagePullFinishedEvent
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp, tz=UTC)
        log.debug("handle_image_pull_finished: ag:{} img:{}, end_dt:{}", ev.agent_id, ev.image, dt)

        image_id = await self._resolve_image_id(ev.image, ev.image_ref)
        await self._schedule_coordinator.update_kernels_to_prepared_for_image(
            ev.agent_id,
            ev.image,
            ev.image_ref.canonical if ev.image_ref else None,
            image_id=image_id,
        )

    async def handle_image_pull_failed(
        self,
        _context: None,
        _agent_id: AgentId,
        ev: ImagePullFailedEvent,
    ) -> None:
        log.warning("handle_image_pull_failed: ag:{} img:{}, msg:{}", ev.agent_id, ev.image, ev.msg)

        image_id = await self._resolve_image_id(ev.image, ev.image_ref)
        await self._schedule_coordinator.cancel_kernels_for_failed_image(
            ev.agent_id,
            ev.image,
            ev.msg,
            ev.image_ref.canonical if ev.image_ref else None,
            image_id=image_id,
        )
