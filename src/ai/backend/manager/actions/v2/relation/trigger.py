from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("RelationActionTriggerMeta",)


@dataclass(frozen=True)
class RelationActionTriggerMeta:
    """What a run of this shape is, handed to its validators and monitors."""

    action_id: ActionID
    started_at: datetime
    scope_targets: Sequence[ScopeRef]
    operation_type: ActionOperationType
    action_name: str
