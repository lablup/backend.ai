from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.notification import NotificationChannelID, NotificationRuleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.manager.data.notification.types import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.models.notification.row import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.models.notification.searchable_fields import (
    NotificationChannelSearchableFields,
    NotificationRuleSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("NotificationChannelUpserter", "NotificationRuleUpserter")


@dataclass
class NotificationChannelUpserter(
    CreatedInGlobal[NotificationChannelRow],
    EntityUpserter[NotificationChannelRow, NotificationChannelData],
):
    """Write a notification channel under its stated id.

    Conflict key: id. ``created_by`` is written on insert only.
    """

    id: NotificationChannelID
    name: str
    channel_type: NotificationChannelType
    spec: WebhookSpec | EmailSpec
    created_by: UserID
    description: str | None
    enabled: bool

    @override
    def entity_id(self, row: NotificationChannelRow) -> NotificationChannelID:
        return NotificationChannelID(row.id)

    @override
    def row_class(self) -> type[NotificationChannelRow]:
        return NotificationChannelRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "created_by": self.created_by, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "channel_type": str(self.channel_type),
            "config": self.spec.model_dump(),
            "enabled": self.enabled,
        }

    @override
    def to_data(self, row: NotificationChannelRow) -> NotificationChannelData:
        return NotificationChannelSearchableFields.own.to_data(row)


@dataclass
class NotificationRuleUpserter(
    CreatedInGlobal[NotificationRuleRow],
    EntityUpserter[NotificationRuleRow, NotificationRuleData],
):
    """Write a notification rule under its stated id.

    Conflict key: id. ``created_by`` is written on insert only.
    """

    id: NotificationRuleID
    name: str
    rule_type: NotificationRuleType
    channel_id: NotificationChannelID
    message_template: str
    created_by: UserID
    description: str | None
    enabled: bool

    @override
    def entity_id(self, row: NotificationRuleRow) -> NotificationRuleID:
        return NotificationRuleID(row.id)

    @override
    def row_class(self) -> type[NotificationRuleRow]:
        return NotificationRuleRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "created_by": self.created_by, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "rule_type": str(self.rule_type),
            "channel_id": self.channel_id,
            "message_template": self.message_template,
            "enabled": self.enabled,
        }

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return NotificationRuleSearchableFields.own.to_data(row)
