from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("SingleEntityActionTriggerMeta",)


@dataclass(frozen=True)
class SingleEntityActionTriggerMeta:
    """What a run of this shape is, handed to its validators and monitors.

    They read the entity from here rather than from the action: a field action's entity
    is looked up rather than declared, so there is no action of this shape to hand over.
    """

    action_id: ActionID
    started_at: datetime
    entity: EntityIdentifier
    operation_type: ActionOperationType
    action_name: str
