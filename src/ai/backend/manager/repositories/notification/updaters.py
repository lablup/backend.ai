from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.notification import WebhookSpec
from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class NotificationChannelUpdaterSpec(UpdaterSpec[NotificationChannelRow]):
    """UpdaterSpec for notification channel updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: OptionalState[str | None] = field(default_factory=OptionalState[str | None].nop)
    spec: OptionalState[WebhookSpec | EmailSpec] = field(
        default_factory=OptionalState[WebhookSpec | EmailSpec].nop
    )
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
        spec_value = self.spec.optional_value()
        if spec_value is not None:
            to_update["config"] = spec_value.model_dump()
        self.enabled.update_dict(to_update, "enabled")
        return to_update


@dataclass
class NotificationRuleUpdaterSpec(UpdaterSpec[NotificationRuleRow]):
    """UpdaterSpec for notification rule updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: OptionalState[str | None] = field(default_factory=OptionalState[str | None].nop)
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
