from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Final

from aiohttp_sse import EventSourceResponse

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.events.hub.propagators.session import SessionEventPropagator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EventsService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db  # SessionEventPropagator requires db directly

    def create_session_propagator(
        self,
        response: EventSourceResponse,
        filters: Mapping[str, Any],
    ) -> SessionEventPropagator:
        return SessionEventPropagator(response, self._db, filters)
