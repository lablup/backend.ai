from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.options import DefaultSessionOptions

from .base import ScalingGroupAction


@dataclass(frozen=True)
class ReplaceDefaultSessionOptionsAction(ScalingGroupAction):
    """Action to fully replace a resource group's ``default_session_options``.

    Admin-only — new sessions created in this resource group will have
    their options resolved with this new default as the fallback layer;
    already-enqueued sessions keep the options frozen onto them at
    their own enqueue time.
    """

    resource_group: ResourceGroupName
    options: DefaultSessionOptions

    @override
    @classmethod
    def action_name(cls) -> str:
        return "replace_resource_group_default_session_options"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class ReplaceDefaultSessionOptionsActionResult:
    """Result of replacing a resource group's ``default_session_options``.

    Carries only the refreshed :class:`DefaultSessionOptions` — callers
    that need the surrounding resource group node are expected to
    re-fetch it.
    """

    resource_group: ResourceGroupName
    options: DefaultSessionOptions
