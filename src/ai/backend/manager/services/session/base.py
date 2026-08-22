from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SessionID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class SessionAction(BaseSingleEntityAction):
    """Base for an operation on one session.

    The name a request carries resolves to this id through the session lookup, so
    what the operation is answered for is the session itself.
    """

    session_id: SessionID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.session_id


@dataclass(frozen=True)
class SessionGlobalAction(BaseGlobalAction):
    """Base for a session operation that names none."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE


@dataclass
class SessionScopeAction(BaseScopeAction):
    """Base for a session operation bounded by a scope rather than one session."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE


@dataclass
class SessionScopeActionResult(BaseScopeActionResult):
    """A scoped session read names no entity."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
