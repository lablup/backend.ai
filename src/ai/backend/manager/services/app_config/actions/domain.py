"""Domain-level app configuration actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec

from .base import AppConfigAction


@dataclass
class GetDomainConfigAction(AppConfigAction):
    """Action to get domain-level app configuration."""

    domain_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_DOMAIN

    @override
    def entity_id(self) -> str | None:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetDomainConfigActionResult(BaseActionResult):
    """Result of get domain config action."""

    result: AppConfigData | None

    @override
    def entity_id(self) -> str | None:
        return self.result.scope_id if self.result else None


@dataclass
class UpsertDomainConfigAction(AppConfigAction):
    """Action to create or update domain-level app configuration."""

    domain_name: str
    updater_spec: AppConfigUpdaterSpec

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_DOMAIN

    @override
    def entity_id(self) -> str | None:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpsertDomainConfigActionResult(BaseActionResult):
    """Result of upsert domain config action."""

    result: AppConfigData

    @override
    def entity_id(self) -> str | None:
        return self.result.scope_id


@dataclass
class DeleteDomainConfigAction(AppConfigAction):
    """Action to delete domain-level app configuration."""

    domain_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.APP_CONFIG_DOMAIN

    @override
    def entity_id(self) -> str | None:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteDomainConfigActionResult(BaseActionResult):
    """Result of delete domain config action."""

    deleted: bool
    domain_name: str

    @override
    def entity_id(self) -> str | None:
        return self.domain_name if self.deleted else None
