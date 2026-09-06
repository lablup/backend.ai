"""The receiving side's answers, and the lending side's withdrawals."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import (
    ENTITY_SHARE_ENTITY_TYPE,
    EntityShareID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.entity_share.types import EntityShareData

__all__ = (
    "AcceptEntityShareAction",
    "CancelEntityShareAction",
    "CancelEntityShareActionResult",
    "EntityShareAnswerResult",
    "LeaveEntityShareAction",
    "RejectEntityShareAction",
    "RevokeEntityShareAction",
    "RevokeEntityShareActionResult",
)


@dataclass
class _RecipientAnswerAction(BaseScopeAction):
    """Base for an answer the receiving side gives.

    Scoped to what answers rather than to the offer: an offer that reached an address
    carries no permission for its recipient to hold, so what is checked is that the
    caller may answer offers at that scope at all. Whether the offer is addressed there
    is decided by the write, whose guard matches the scope.
    """

    share_id: EntityShareID
    answering_scope: EntityIdentifier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ENTITY_SHARE_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        scope = self.answering_scope
        return (ScopeRef(scope_type=ScopeType(scope.entity_type()), scope_id=scope),)


@dataclass
class AcceptEntityShareAction(_RecipientAnswerAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "accept_entity_share"


@dataclass
class RejectEntityShareAction(_RecipientAnswerAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "reject_entity_share"


@dataclass
class EntityShareAnswerResult(BaseScopeActionResult):
    """What the answer settled.

    The run was requested within the answering person's scope while what it touched is
    the invitation, so that is what the audit trail is keyed on.
    """

    data: EntityShareData

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return (self.data.id,)


@dataclass
class CancelEntityShareAction(BaseSingleEntityAction):
    """Withdraw an offer before it was answered.

    Named on the invitation itself: whoever may reach the entity it offers may reach
    the invitation, so there is a permission to check here.
    """

    share_id: EntityShareID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "cancel_entity_share"

    @override
    def entity_id(self) -> EntityShareID:
        return self.share_id


@dataclass
class CancelEntityShareActionResult:
    """The withdrawn invitation. The shape already names it, so nothing is restated."""

    data: EntityShareData


@dataclass
class LeaveEntityShareAction(_RecipientAnswerAction):
    """The receiving side gives back what it took."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "leave_entity_share"


@dataclass
class RevokeEntityShareAction(BaseSingleEntityAction):
    """Take back what was lent.

    Named on the share itself: whoever may reach the entity it lends may reach the
    share, so there is a permission to check here.
    """

    share_id: EntityShareID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "revoke_entity_share"

    @override
    def entity_id(self) -> EntityShareID:
        return self.share_id


@dataclass
class RevokeEntityShareActionResult:
    """The share that was taken back."""

    data: EntityShareData
