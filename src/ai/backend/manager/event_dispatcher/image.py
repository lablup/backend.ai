import logging
from datetime import datetime

from ai.backend.common.events.image import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.registry import AgentRegistry

from ..models.utils import (
    ExtendedAsyncSAEngine,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ImageEventHandler:
    def __init__(self, registry: AgentRegistry, db: ExtendedAsyncSAEngine) -> None:
        self._registry = registry
        self._db = db

    async def handle_image_pull_started(
        self,
        context: None,
        agent_id: AgentId,
        ev: ImagePullStartedEvent,
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp)
        log.debug("handle_image_pull_started: ag:{} img:{}, start_dt:{}", ev.agent_id, ev.image, dt)
        async with self._db.connect() as db_conn:
            await self._registry.mark_image_pull_started(
                ev.agent_id, ev.image, ev.image_ref, db_conn=db_conn
            )

    async def handle_image_pull_finished(
        self, context: None, agent_id: AgentId, ev: ImagePullFinishedEvent
    ) -> None:
        dt = datetime.fromtimestamp(ev.timestamp)
        log.debug("handle_image_pull_finished: ag:{} img:{}, end_dt:{}", ev.agent_id, ev.image, dt)
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
        async with self._db.connect() as db_conn:
            await self._registry.handle_image_pull_failed(
                ev.agent_id, ev.image, ev.msg, ev.image_ref, db_conn=db_conn
            )
