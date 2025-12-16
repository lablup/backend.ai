from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from typing_extensions import override

from ai.backend.manager.data.notification.types import WebhookConfig
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class NotificationChannelUpdaterSpec(UpdaterSpec[NotificationChannelRow]):
    """UpdaterSpec for notification channel updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: OptionalState[Optional[str]] = field(
        default_factory=OptionalState[Optional[str]].nop
    )
    config: OptionalState[WebhookConfig] = field(default_factory=OptionalState[WebhookConfig].nop)
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[NotificationChannelRow]:
        return NotificationChannelRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        config_value = self.config.optional_value()
        if config_value is not None:
            to_update["config"] = config_value.model_dump()
        self.enabled.update_dict(to_update, "enabled")
        return to_update


@dataclass
class NotificationRuleUpdaterSpec(UpdaterSpec[NotificationRuleRow]):
    """UpdaterSpec for notification rule updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: OptionalState[Optional[str]] = field(
        default_factory=OptionalState[Optional[str]].nop
    )
    message_template: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[NotificationRuleRow]:
        return NotificationRuleRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.message_template.update_dict(to_update, "message_template")
        self.enabled.update_dict(to_update, "enabled")
        return to_update
