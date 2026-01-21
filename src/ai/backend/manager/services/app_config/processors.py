"""Processors for app configuration service."""

from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from .actions import (
    DeleteDomainConfigAction,
    DeleteDomainConfigActionResult,
    DeleteUserConfigAction,
    DeleteUserConfigActionResult,
    GetDomainConfigAction,
    GetDomainConfigActionResult,
    GetMergedAppConfigAction,
    GetMergedAppConfigActionResult,
    GetUserConfigAction,
    GetUserConfigActionResult,
    UpsertDomainConfigAction,
    UpsertDomainConfigActionResult,
    UpsertUserConfigAction,
    UpsertUserConfigActionResult,
)
from .service import AppConfigService


class AppConfigProcessors(AbstractProcessorPackage):
    """Processors for app configuration operations."""

    # Domain config processors
    get_domain_config: ActionProcessor[GetDomainConfigAction, GetDomainConfigActionResult]
    upsert_domain_config: ActionProcessor[UpsertDomainConfigAction, UpsertDomainConfigActionResult]
    delete_domain_config: ActionProcessor[DeleteDomainConfigAction, DeleteDomainConfigActionResult]

    # User config processors
    get_user_config: ActionProcessor[GetUserConfigAction, GetUserConfigActionResult]
    upsert_user_config: ActionProcessor[UpsertUserConfigAction, UpsertUserConfigActionResult]
    delete_user_config: ActionProcessor[DeleteUserConfigAction, DeleteUserConfigActionResult]

    # Merged config processor
    get_merged_config: ActionProcessor[GetMergedAppConfigAction, GetMergedAppConfigActionResult]

    def __init__(self, service: AppConfigService, action_monitors: list[ActionMonitor]) -> None:
        # Domain config processors
        self.get_domain_config = ActionProcessor(service.get_domain_config, action_monitors)
        self.upsert_domain_config = ActionProcessor(service.upsert_domain_config, action_monitors)
        self.delete_domain_config = ActionProcessor(service.delete_domain_config, action_monitors)

        # User config processors
        self.get_user_config = ActionProcessor(service.get_user_config, action_monitors)
        self.upsert_user_config = ActionProcessor(service.upsert_user_config, action_monitors)
        self.delete_user_config = ActionProcessor(service.delete_user_config, action_monitors)

        # Merged config processor
        self.get_merged_config = ActionProcessor(service.get_merged_config, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            # Domain config actions
            GetDomainConfigAction.spec(),
            UpsertDomainConfigAction.spec(),
            DeleteDomainConfigAction.spec(),
            # User config actions
            GetUserConfigAction.spec(),
            UpsertUserConfigAction.spec(),
            DeleteUserConfigAction.spec(),
            # Merged config action
            GetMergedAppConfigAction.spec(),
        ]
