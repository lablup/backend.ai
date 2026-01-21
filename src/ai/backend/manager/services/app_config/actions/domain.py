"""Domain-level app configuration actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec

from .base import AppConfigAction


@dataclass
class GetDomainConfigAction(AppConfigAction):
    """Action to get domain-level app configuration."""

    domain_name: str

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "app_config_domain"

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_domain_config"


@dataclass
class GetDomainConfigActionResult(BaseActionResult):
    """Result of get domain config action."""

    result: Optional[AppConfigData]

    @override
    def entity_id(self) -> Optional[str]:
        return self.result.scope_id if self.result else None


@dataclass
class UpsertDomainConfigAction(AppConfigAction):
    """Action to create or update domain-level app configuration."""

    domain_name: str
    updater_spec: AppConfigUpdaterSpec

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "app_config_domain"

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "upsert_domain_config"


@dataclass
class UpsertDomainConfigActionResult(BaseActionResult):
    """Result of upsert domain config action."""

    result: AppConfigData

    @override
    def entity_id(self) -> Optional[str]:
        return self.result.scope_id


@dataclass
class DeleteDomainConfigAction(AppConfigAction):
    """Action to delete domain-level app configuration."""

    domain_name: str

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "app_config_domain"

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_domain_config"


@dataclass
class DeleteDomainConfigActionResult(BaseActionResult):
    """Result of delete domain config action."""

    deleted: bool
    domain_name: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_name if self.deleted else None
