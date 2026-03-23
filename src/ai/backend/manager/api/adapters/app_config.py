"""App configuration domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from typing import Any

from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    DeleteDomainConfigPayload,
    DeleteUserConfigPayload,
)
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec
from ai.backend.manager.services.app_config.actions import (
    DeleteDomainConfigAction,
    DeleteUserConfigAction,
    GetDomainConfigAction,
    GetMergedAppConfigAction,
    GetUserConfigAction,
    UpsertDomainConfigAction,
    UpsertUserConfigAction,
)
from ai.backend.manager.types import OptionalState

from .base import BaseAdapter


class AppConfigAdapter(BaseAdapter):
    """Adapter for app configuration domain operations."""

    async def get_domain_config(self, domain_name: str) -> AppConfigNode | None:
        """Get domain-level app configuration."""
        action_result = await self._processors.app_config.get_domain_config.wait_for_complete(
            GetDomainConfigAction(domain_name=domain_name)
        )
        if not action_result.result:
            return None
        return self._data_to_dto(action_result.result)

    async def upsert_domain_config(
        self, domain_name: str, extra_config: dict[str, Any]
    ) -> AppConfigNode:
        """Create or update domain-level app configuration."""
        action_result = await self._processors.app_config.upsert_domain_config.wait_for_complete(
            UpsertDomainConfigAction(
                domain_name=domain_name,
                updater_spec=AppConfigUpdaterSpec(extra_config=OptionalState.update(extra_config)),
            )
        )
        return self._data_to_dto(action_result.result)

    async def delete_domain_config(self, domain_name: str) -> DeleteDomainConfigPayload:
        """Delete domain-level app configuration."""
        action_result = await self._processors.app_config.delete_domain_config.wait_for_complete(
            DeleteDomainConfigAction(domain_name=domain_name)
        )
        return DeleteDomainConfigPayload(deleted=action_result.deleted)

    async def get_user_config(self, user_id: str) -> AppConfigNode | None:
        """Get user-level app configuration."""
        action_result = await self._processors.app_config.get_user_config.wait_for_complete(
            GetUserConfigAction(user_id=user_id)
        )
        if not action_result.result:
            return None
        return self._data_to_dto(action_result.result)

    async def upsert_user_config(self, user_id: str, extra_config: dict[str, Any]) -> AppConfigNode:
        """Create or update user-level app configuration."""
        action_result = await self._processors.app_config.upsert_user_config.wait_for_complete(
            UpsertUserConfigAction(
                user_id=user_id,
                updater_spec=AppConfigUpdaterSpec(extra_config=OptionalState.update(extra_config)),
            )
        )
        return self._data_to_dto(action_result.result)

    async def delete_user_config(self, user_id: str) -> DeleteUserConfigPayload:
        """Delete user-level app configuration."""
        action_result = await self._processors.app_config.delete_user_config.wait_for_complete(
            DeleteUserConfigAction(user_id=user_id)
        )
        return DeleteUserConfigPayload(deleted=action_result.deleted)

    async def get_merged_config(self, user_id: str) -> AppConfigNode:
        """Get merged app configuration for a user."""
        action_result = await self._processors.app_config.get_merged_config.wait_for_complete(
            GetMergedAppConfigAction(user_id=user_id)
        )
        return AppConfigNode(extra_config=dict(action_result.merged_config))

    @staticmethod
    def _data_to_dto(data: AppConfigData) -> AppConfigNode:
        """Convert data layer type to Pydantic DTO."""
        return AppConfigNode(extra_config=data.extra_config)
