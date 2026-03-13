from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Final

from aiohttp_sse import EventSourceResponse

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.events.hub.propagators.session import SessionEventPropagator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.events.repository import EventsRepository
from ai.backend.manager.services.events.actions.resolve_group_for_events import (
    ResolveGroupForEventsAction,
    ResolveGroupForEventsActionResult,
)
from ai.backend.manager.services.events.actions.resolve_session_for_events import (
    ResolveSessionForEventsAction,
    ResolveSessionForEventsActionResult,
)

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EventsService:
    _repository: EventsRepository
    _db: ExtendedAsyncSAEngine

    def __init__(self, repository: EventsRepository, db: ExtendedAsyncSAEngine) -> None:
        self._repository = repository
        self._db = db  # SessionEventPropagator requires db directly

    async def resolve_session_for_events(
        self, action: ResolveSessionForEventsAction
    ) -> ResolveSessionForEventsActionResult:
        rows = await self._repository.match_sessions_by_name(
            action.session_name, AccessKey(action.access_key)
        )
        if not rows:
            raise SessionNotFound
        return ResolveSessionForEventsActionResult(session_id=rows[0].id)

    async def resolve_group_for_events(
        self, action: ResolveGroupForEventsAction
    ) -> ResolveGroupForEventsActionResult:
        group_id = await self._repository.resolve_group_id(action.group_name)
        return ResolveGroupForEventsActionResult(group_id=group_id)

    def create_session_propagator(
        self,
        response: EventSourceResponse,
        filters: Mapping[str, Any],
    ) -> SessionEventPropagator:
        return SessionEventPropagator(response, self._db, filters)
