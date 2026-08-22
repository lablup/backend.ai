from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.action import ActionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("BulkActionTriggerMeta",)


@dataclass(frozen=True)
class BulkActionTriggerMeta:
    """What a run of this shape is, handed to its validators and monitors.

    They read the entities from here rather than from the action: a field bulk names
    rows whose membership is only knowable through their owners, so those entities are
    read before anything is checked or recorded.
    """

    action_id: ActionID
    started_at: datetime
    entity_ids: Sequence[EntityIdentifier]
    operation_type: ActionOperationType
    action_name: str
