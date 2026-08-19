from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class GCStaleConnectionsAction(BaseGlobalAction):
    """Drop the tracked stream connections whose sessions are gone.

    Runs on the installation's connection table rather than on any session, which is
    why it names none.
    """

    active_session_ids: list[SessionId]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_gc_stale_stream_connections"


@dataclass(frozen=True)
class GCStaleConnectionsActionResult:
    inactive_session_ids: list[SessionId]
