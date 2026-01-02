from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from typing_extensions import override

from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class NotificationChannelData:
    """Domain model data for notification channel."""

    id: UUID
    name: str
    description: Optional[str]
    channel_type: NotificationChannelType
    config: WebhookConfig
    enabled: bool
    created_by: UUID
    created_at: datetime = field(compare=False)
    updated_at: datetime = field(compare=False)


@dataclass
class NotificationRuleData:
    """Domain model data for notification rule."""

    id: UUID
    name: str
    description: Optional[str]
    rule_type: NotificationRuleType
    channel: NotificationChannelData
    message_template: str
    enabled: bool
    created_by: UUID
    created_at: datetime = field(compare=False)
    updated_at: datetime = field(compare=False)


@dataclass
class NotificationChannelModifier(PartialModifier):
    """Modifier for notification channel."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: OptionalState[Optional[str]] = field(
        default_factory=OptionalState[Optional[str]].nop
    )
    config: OptionalState[WebhookConfig] = field(default_factory=OptionalState[WebhookConfig].nop)
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        config_value = self.config.optional_value()
        if config_value is not None:
            to_update["config"] = config_value.model_dump()
        self.enabled.update_dict(to_update, "enabled")
        return to_update


@dataclass
class NotificationRuleModifier(PartialModifier):
    """Modifier for notification rule."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: OptionalState[Optional[str]] = field(
        default_factory=OptionalState[Optional[str]].nop
    )
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
