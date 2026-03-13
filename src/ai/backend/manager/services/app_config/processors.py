"""Processors for app configuration service."""

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators

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
    get_domain_config: ScopeActionProcessor[GetDomainConfigAction, GetDomainConfigActionResult]
    upsert_domain_config: ScopeActionProcessor[
        UpsertDomainConfigAction, UpsertDomainConfigActionResult
    ]
    delete_domain_config: ScopeActionProcessor[
        DeleteDomainConfigAction, DeleteDomainConfigActionResult
    ]

    # User config processors
    get_user_config: ScopeActionProcessor[GetUserConfigAction, GetUserConfigActionResult]
    upsert_user_config: ScopeActionProcessor[UpsertUserConfigAction, UpsertUserConfigActionResult]
    delete_user_config: ScopeActionProcessor[DeleteUserConfigAction, DeleteUserConfigActionResult]

    # Merged config processor
    get_merged_config: ScopeActionProcessor[
        GetMergedAppConfigAction, GetMergedAppConfigActionResult
    ]

    def __init__(
        self,
        service: AppConfigService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Domain config processors
        self.get_domain_config = ScopeActionProcessor(
            service.get_domain_config, action_monitors, validators=[validators.rbac.scope]
        )
        self.upsert_domain_config = ScopeActionProcessor(
            service.upsert_domain_config, action_monitors, validators=[validators.rbac.scope]
        )
        self.delete_domain_config = ScopeActionProcessor(
            service.delete_domain_config, action_monitors, validators=[validators.rbac.scope]
        )

        # User config processors
        self.get_user_config = ScopeActionProcessor(
            service.get_user_config, action_monitors, validators=[validators.rbac.scope]
        )
        self.upsert_user_config = ScopeActionProcessor(
            service.upsert_user_config, action_monitors, validators=[validators.rbac.scope]
        )
        self.delete_user_config = ScopeActionProcessor(
            service.delete_user_config, action_monitors, validators=[validators.rbac.scope]
        )

        # Merged config processor
        self.get_merged_config = ScopeActionProcessor(
            service.get_merged_config, action_monitors, validators=[validators.rbac.scope]
        )

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
