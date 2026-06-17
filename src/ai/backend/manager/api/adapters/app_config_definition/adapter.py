"""App config definition adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.app_config_definition.request import (
    CreateAppConfigDefinitionInput,
    SearchAppConfigDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.app_config_definition.response import (
    AppConfigDefinitionNode,
    CreateAppConfigDefinitionPayload,
    PurgeAppConfigDefinitionPayload,
    SearchAppConfigDefinitionsPayload,
)
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.app_config_definition.creators import (
    AppConfigDefinitionCreatorSpec,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.app_config_definition.actions.create import (
    CreateAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.get import (
    GetAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.purge import (
    PurgeAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.search import (
    SearchAppConfigDefinitionsAction,
)

DEFAULT_PAGINATION_LIMIT = 50


class AppConfigDefinitionAdapter(BaseAdapter):
    """Adapter for app config definition domain operations (admin-only)."""

    @staticmethod
    def _data_to_node(data: AppConfigDefinitionData) -> AppConfigDefinitionNode:
        return AppConfigDefinitionNode(
            id=data.id,
            config_name=data.config_name,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    async def admin_create(
        self, input: CreateAppConfigDefinitionInput
    ) -> CreateAppConfigDefinitionPayload:
        creator = Creator[AppConfigDefinitionRow](
            spec=AppConfigDefinitionCreatorSpec(config_name=input.config_name),
        )
        action_result = await self._processors.app_config_definition.create.wait_for_complete(
            CreateAppConfigDefinitionAction(creator=creator)
        )
        return CreateAppConfigDefinitionPayload(
            app_config_definition=self._data_to_node(action_result.definition),
        )

    async def admin_get(self, definition_id: UUID) -> AppConfigDefinitionNode:
        action_result = await self._processors.app_config_definition.get.wait_for_complete(
            GetAppConfigDefinitionAction(definition_id=AppConfigDefinitionID(definition_id))
        )
        return self._data_to_node(action_result.definition)

    async def admin_search(
        self, input: SearchAppConfigDefinitionsInput
    ) -> SearchAppConfigDefinitionsPayload:
        pagination = OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )
        action_result = await self._processors.app_config_definition.search.wait_for_complete(
            SearchAppConfigDefinitionsAction(querier=BatchQuerier(pagination=pagination))
        )
        return SearchAppConfigDefinitionsPayload(
            items=[self._data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def admin_purge(self, definition_id: UUID) -> PurgeAppConfigDefinitionPayload:
        purger = Purger[AppConfigDefinitionRow](
            row_class=AppConfigDefinitionRow,
            pk_value=AppConfigDefinitionID(definition_id),
        )
        action_result = await self._processors.app_config_definition.purge.wait_for_complete(
            PurgeAppConfigDefinitionAction(purger=purger)
        )
        return PurgeAppConfigDefinitionPayload(id=action_result.definition.id)
