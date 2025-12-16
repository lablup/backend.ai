"""Service layer for app configuration operations."""

from __future__ import annotations

import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.app_config import AppConfigScopeType
from ai.backend.manager.repositories.app_config import AppConfigRepository

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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AppConfigService:
    """Service for app configuration operations."""

    _app_config_repository: AppConfigRepository

    def __init__(
        self,
        app_config_repository: AppConfigRepository,
    ) -> None:
        self._app_config_repository = app_config_repository

    # Domain config operations

    async def get_domain_config(self, action: GetDomainConfigAction) -> GetDomainConfigActionResult:
        """Get domain-level app configuration."""
        log.debug("Getting domain config for: {}", action.domain_name)
        config_data = await self._app_config_repository.get_config(
            AppConfigScopeType.DOMAIN,
            action.domain_name,
        )
        return GetDomainConfigActionResult(result=config_data)

    async def upsert_domain_config(
        self, action: UpsertDomainConfigAction
    ) -> UpsertDomainConfigActionResult:
        """Create or update domain-level app configuration."""
        log.debug("Upserting domain config for: {}", action.domain_name)
        config_data = await self._app_config_repository.upsert_config(
            AppConfigScopeType.DOMAIN,
            action.domain_name,
            action.updater_spec,
        )
        return UpsertDomainConfigActionResult(result=config_data)

    async def delete_domain_config(
        self, action: DeleteDomainConfigAction
    ) -> DeleteDomainConfigActionResult:
        """Delete domain-level app configuration."""
        log.debug("Deleting domain config for: {}", action.domain_name)
        deleted = await self._app_config_repository.delete_config(
            AppConfigScopeType.DOMAIN,
            action.domain_name,
        )
        return DeleteDomainConfigActionResult(
            deleted=deleted,
            domain_name=action.domain_name,
        )

    # User config operations

    async def get_user_config(self, action: GetUserConfigAction) -> GetUserConfigActionResult:
        """Get user-level app configuration."""
        log.debug("Getting user config for: {}", action.user_id)
        config_data = await self._app_config_repository.get_config(
            AppConfigScopeType.USER,
            action.user_id,
        )
        return GetUserConfigActionResult(result=config_data)

    async def upsert_user_config(
        self, action: UpsertUserConfigAction
    ) -> UpsertUserConfigActionResult:
        """Create or update user-level app configuration."""
        log.debug("Upserting user config for: {}", action.user_id)
        config_data = await self._app_config_repository.upsert_config(
            AppConfigScopeType.USER,
            action.user_id,
            action.updater_spec,
        )
        return UpsertUserConfigActionResult(result=config_data)

    async def delete_user_config(
        self, action: DeleteUserConfigAction
    ) -> DeleteUserConfigActionResult:
        """Delete user-level app configuration."""
        log.debug("Deleting user config for: {}", action.user_id)
        deleted = await self._app_config_repository.delete_config(
            AppConfigScopeType.USER,
            action.user_id,
        )
        return DeleteUserConfigActionResult(
            deleted=deleted,
            user_id=action.user_id,
        )

    # Merged config operation

    async def get_merged_config(
        self, action: GetMergedAppConfigAction
    ) -> GetMergedAppConfigActionResult:
        """
        Get merged app configuration for a user.
        Domain config is merged with user config (user overrides domain).
        """
        log.debug("Getting merged app config for user: {}", action.user_id)
        merged_config = await self._app_config_repository.get_merged_config(action.user_id)
        return GetMergedAppConfigActionResult(
            user_id=action.user_id,
            merged_config=merged_config,
        )
