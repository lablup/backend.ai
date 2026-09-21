"""What a notification search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import assert_never, override

from ai.backend.common.data.entity.notification import (
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.common.data.notification import (
    EmailSpec,
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.models.notification.row import (
    NotificationChannelRow,
    NotificationRuleRow,
)
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _NotificationChannelOwnFields(
    RowDataConverter[NotificationChannelRow, NotificationChannelData]
):
    """The notification channel's own columns."""

    id = SearchableField(
        NotificationChannelRow.id,
        UUIDConditions(NotificationChannelRow.id),
        ColumnOrder(NotificationChannelRow.id),
    )
    name = SearchableField(
        NotificationChannelRow.name,
        StringConditions(NotificationChannelRow.name),
        ColumnOrder(NotificationChannelRow.name),
    )
    description = SearchableField(
        NotificationChannelRow.description,
        StringEqualityConditions(NotificationChannelRow.description),
        ColumnOrder(NotificationChannelRow.description),
    )
    channel_type = SearchableField(
        NotificationChannelRow.channel_type,
        EnumConditions(NotificationChannelRow.channel_type, NotificationChannelType),
        ColumnOrder(NotificationChannelRow.channel_type),
    )
    config = SearchableField(NotificationChannelRow.config, None, None)
    """Impossible: a JSON document of the channel's delivery settings."""
    enabled = SearchableField(
        NotificationChannelRow.enabled,
        BoolConditions(NotificationChannelRow.enabled),
        ColumnOrder(NotificationChannelRow.enabled),
    )
    created_by = SearchableField(
        NotificationChannelRow.created_by,
        UUIDConditions(NotificationChannelRow.created_by),
        ColumnOrder(NotificationChannelRow.created_by),
    )
    created_at = SearchableField(
        NotificationChannelRow.created_at,
        DateTimeConditions(NotificationChannelRow.created_at),
        ColumnOrder(NotificationChannelRow.created_at),
    )
    updated_at = SearchableField(
        NotificationChannelRow.updated_at,
        DateTimeConditions(NotificationChannelRow.updated_at),
        ColumnOrder(NotificationChannelRow.updated_at),
    )

    @override
    def to_data(self, row: NotificationChannelRow) -> NotificationChannelData:
        channel_type = NotificationChannelType(self.channel_type.read(row))
        spec: WebhookSpec | EmailSpec
        match channel_type:
            case NotificationChannelType.WEBHOOK:
                spec = WebhookSpec.model_validate(self.config.read(row))
            case NotificationChannelType.EMAIL:
                spec = EmailSpec.model_validate(self.config.read(row))
            case _:
                assert_never(channel_type)
        return NotificationChannelData(
            id=NotificationChannelID(self.id.read(row)),
            name=self.name.read(row),
            description=self.description.read(row),
            channel_type=channel_type,
            spec=spec,
            enabled=self.enabled.read(row),
            created_by=self.created_by.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class NotificationChannelSearchableFields:
    own = _NotificationChannelOwnFields()


class _NotificationRuleOwnFields(RowDataConverter[NotificationRuleRow, NotificationRuleData]):
    """The notification rule's own columns."""

    id = SearchableField(
        NotificationRuleRow.id,
        UUIDConditions(NotificationRuleRow.id),
        ColumnOrder(NotificationRuleRow.id),
    )
    name = SearchableField(
        NotificationRuleRow.name,
        StringConditions(NotificationRuleRow.name),
        ColumnOrder(NotificationRuleRow.name),
    )
    description = SearchableField(
        NotificationRuleRow.description,
        StringEqualityConditions(NotificationRuleRow.description),
        ColumnOrder(NotificationRuleRow.description),
    )
    rule_type = SearchableField(
        NotificationRuleRow.rule_type,
        EnumConditions(NotificationRuleRow.rule_type, NotificationRuleType),
        ColumnOrder(NotificationRuleRow.rule_type),
    )
    channel_id = SearchableField(
        NotificationRuleRow.channel_id,
        UUIDConditions(NotificationRuleRow.channel_id),
        ColumnOrder(NotificationRuleRow.channel_id),
    )
    message_template = SearchableField(
        NotificationRuleRow.message_template,
        StringEqualityConditions(NotificationRuleRow.message_template),
        ColumnOrder(NotificationRuleRow.message_template),
    )
    enabled = SearchableField(
        NotificationRuleRow.enabled,
        BoolConditions(NotificationRuleRow.enabled),
        ColumnOrder(NotificationRuleRow.enabled),
    )
    created_by = SearchableField(
        NotificationRuleRow.created_by,
        UUIDConditions(NotificationRuleRow.created_by),
        ColumnOrder(NotificationRuleRow.created_by),
    )
    created_at = SearchableField(
        NotificationRuleRow.created_at,
        DateTimeConditions(NotificationRuleRow.created_at),
        ColumnOrder(NotificationRuleRow.created_at),
    )
    updated_at = SearchableField(
        NotificationRuleRow.updated_at,
        DateTimeConditions(NotificationRuleRow.updated_at),
        ColumnOrder(NotificationRuleRow.updated_at),
    )

    @override
    def to_data(self, row: NotificationRuleRow) -> NotificationRuleData:
        return NotificationRuleData(
            id=NotificationRuleID(self.id.read(row)),
            name=self.name.read(row),
            description=self.description.read(row),
            rule_type=NotificationRuleType(self.rule_type.read(row)),
            channel_id=NotificationChannelID(self.channel_id.read(row)),
            message_template=self.message_template.read(row),
            enabled=self.enabled.read(row),
            created_by=self.created_by.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class NotificationRuleSearchableFields:
    own = _NotificationRuleOwnFields()
