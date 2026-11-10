from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("MembershipActionTriggerMeta",)


@dataclass(frozen=True)
class MembershipActionTriggerMeta:
    """What a run of this shape is, handed to its validators and monitors."""

    action_id: ActionID
    started_at: datetime
    entity: EntityIdentifier
    scopes: Sequence[EntityIdentifier]
    operation_type: ActionOperationType
    action_name: str
