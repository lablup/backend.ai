"""App config adapter bridging v2 DTOs and the merged-config (read) Processors."""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.app_config.types import AppConfigScopeType as AppConfigScopeTypeDTO
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    GetAppConfigsPayload,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.common.exception import UnreachableError
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config.types import AppConfigData
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.services.app_config.actions.get import GetAppConfigsAction


class AppConfigAdapter(BaseAdapter):
    """Adapter for the merged AppConfig (read) operations."""

    # --- merged AppConfig read ---

    async def my_get_app_configs(self, input: MyGetAppConfigsInput) -> GetAppConfigsPayload:
        """The acting user's merged AppConfigs.

        Calls ``current_user()`` internally — the caller does not pass a scope.
        """
        me = current_user()
        if me is None:
            # ``auth_required`` guarantees a session on this route, so this is never hit.
            raise UnreachableError("User context is not available")
        action_result = await self._processors.app_config.get_app_configs.wait_for_complete(
            GetAppConfigsAction(config_names=input.config_names, user_id=UserID(me.user_id))
        )
        return GetAppConfigsPayload(
            app_configs=[
                self._app_config_to_node(app_config) for app_config in action_result.app_configs
            ]
        )

    async def public_get_app_configs(self, input: PublicGetAppConfigsInput) -> GetAppConfigsPayload:
        # Naming no principal is what makes this the anonymous read: only public contributes.
        action_result = await self._processors.app_config.get_app_configs.wait_for_complete(
            GetAppConfigsAction(config_names=input.config_names)
        )
        return GetAppConfigsPayload(
            app_configs=[
                self._app_config_to_node(app_config) for app_config in action_result.app_configs
            ]
        )

    # --- guards / converters ---

    @staticmethod
    def _fragment_to_node(data: AppConfigFragmentData) -> AppConfigFragmentNode:
        return AppConfigFragmentNode(
            id=data.id,
            config_name=data.config_name,
            scope_type=AppConfigScopeTypeDTO(data.scope_type.value),
            scope_id=data.scope_id,
            config=data.config,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @classmethod
    def _app_config_to_node(cls, data: AppConfigData) -> AppConfigNode:
        return AppConfigNode(
            config_name=data.config_name,
            merged_config=data.merged_config,
            fragments=[cls._fragment_to_node(fragment) for fragment in data.fragments],
        )
