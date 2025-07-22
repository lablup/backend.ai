import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BaseActionTriggerMeta:
    action_id: uuid.UUID
    started_at: datetime
