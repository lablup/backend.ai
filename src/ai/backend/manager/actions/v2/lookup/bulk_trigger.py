from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("BulkLookupActionTriggerMeta",)


@dataclass(frozen=True)
class BulkLookupActionTriggerMeta:
    """What a run of this shape is, handed to its validators and monitors."""

    action_id: ActionID
    started_at: datetime
    entity_type: EntityType
    operation_type: ActionOperationType
    action_name: str
