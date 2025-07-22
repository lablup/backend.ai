import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ai.backend.common.json import dump_json_str


class MultiEntityFailureHandlingPolicy(enum.StrEnum):
    ALL_OR_NONE = "all_or_none"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class BaseActionTriggerMeta:
    action_id: uuid.UUID
    started_at: datetime


@dataclass
class ActionTarget:
    entity_type: str
    entity_ids: Optional[list[str]] = None
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None

    def to_json_str(self) -> str:
        return dump_json_str({
            "entity_type": self.entity_type,
            "entity_ids": self.entity_ids,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
        })
