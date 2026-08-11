from typing import NewType
from uuid import UUID

__all__ = (
    "NotificationChannelID",
    "NotificationRuleID",
)


NotificationChannelID = NewType("NotificationChannelID", UUID)
NotificationRuleID = NewType("NotificationRuleID", UUID)
