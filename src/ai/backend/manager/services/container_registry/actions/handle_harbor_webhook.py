from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ContainerRegistryAction


@dataclass
class HarborWebhookResourceInput:
    """A single resource from a Harbor webhook payload."""

    resource_url: str
    tag: str


@dataclass
class HandleHarborWebhookAction(ContainerRegistryAction):
    """Action to handle a Harbor container registry webhook event."""

    event_type: str
    resources: list[HarborWebhookResourceInput] = field(default_factory=list)
    project: str = ""
    img_name: str = ""
    auth_header: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class HandleHarborWebhookActionResult(BaseActionResult):
    """Result of handling a Harbor webhook event."""

    @override
    def entity_id(self) -> str | None:
        return None
