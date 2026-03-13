"""Domain-level app configuration actions."""

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec
from ai.backend.manager.services.app_config.actions.base import (
    AppConfigScopeAction,
    AppConfigScopeActionResult,
)


@dataclass
class GetDomainConfigAction(AppConfigScopeAction):
    """Action to get domain-level app configuration."""

    domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain_name)


@dataclass
class GetDomainConfigActionResult(AppConfigScopeActionResult):
    """Result of get domain config action."""

    result: AppConfigData | None

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.result.scope_id if self.result else ""


@dataclass
class UpsertDomainConfigAction(AppConfigScopeAction):
    """Action to create or update domain-level app configuration."""

    domain_name: str
    updater_spec: AppConfigUpdaterSpec

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain_name)


@dataclass
class UpsertDomainConfigActionResult(AppConfigScopeActionResult):
    """Result of upsert domain config action."""

    result: AppConfigData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.result.scope_id


@dataclass
class DeleteDomainConfigAction(AppConfigScopeAction):
    """Action to delete domain-level app configuration."""

    domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.domain_name

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DOMAIN, self.domain_name)


@dataclass
class DeleteDomainConfigActionResult(AppConfigScopeActionResult):
    """Result of delete domain config action."""

    deleted: bool
    domain_name: str

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.DOMAIN

    @override
    def scope_id(self) -> str:
        return self.domain_name
