from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.notification import (
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier
from ai.backend.common.data.notification import (
    EmailSpec,
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass(frozen=True)
class NotificationChannelData(EntityData):
    """Domain model data for notification channel."""

    id: NotificationChannelID
    name: str
    description: str | None
    channel_type: NotificationChannelType
    spec: WebhookSpec | EmailSpec
    enabled: bool
    created_by: UUID
    created_at: datetime = field(compare=False)
    updated_at: datetime = field(compare=False)

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass(frozen=True)
class NotificationRuleData(EntityData):
    """Domain model data for notification rule.

    Names its channel by id: a row projection mirrors one table, and composing the two
    forced an eager load on every read.
    """

    id: NotificationRuleID
    name: str
    description: str | None
    rule_type: NotificationRuleType
    channel_id: NotificationChannelID
    message_template: str
    enabled: bool
    created_by: UUID
    created_at: datetime = field(compare=False)
    updated_at: datetime = field(compare=False)

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass(frozen=True)
class MatchingNotificationRuleData:
    """A rule paired with the channel it dispatches through.

    Assembled by the repository for the dispatch read, not projected from a row —
    which is why it may carry another entity where a row projection may not.
    """

    rule: NotificationRuleData
    channel: NotificationChannelData


@dataclass
class NotificationChannelModifier(PartialModifier):
    """Modifier for notification channel."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    spec: OptionalState[WebhookSpec | EmailSpec] = field(
        default_factory=OptionalState[WebhookSpec | EmailSpec].nop
    )
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        spec_value = self.spec.optional_value()
        if spec_value is not None:
            to_update["spec"] = spec_value.model_dump()
        self.enabled.update_dict(to_update, "enabled")
        return to_update


@dataclass
class NotificationRuleModifier(PartialModifier):
    """Modifier for notification rule."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    message_template: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.message_template.update_dict(to_update, "message_template")
        self.enabled.update_dict(to_update, "enabled")
        return to_update


@dataclass
class NotificationChannelListResult:
    """Search result with total count for notification channels."""

    items: list[NotificationChannelData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class NotificationRuleListResult:
    """Search result with total count for notification rules."""

    items: list[NotificationRuleData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
