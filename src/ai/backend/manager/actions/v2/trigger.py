from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.entity.action import ActionID

__all__ = ("ActionTriggerMeta",)


@dataclass(frozen=True)
class ActionTriggerMeta:
    """Which run this is, handed to its validators and monitors before it executes.

    Shapes whose action declares its own targets carry nothing further here; the ones
    that look their targets up have their own trigger meta beside this.
    """

    action_id: ActionID
    started_at: datetime
