"""Tests for AppConfigDefinitionService with a mocked repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config_definition.types import (
    AppConfigDefinitionData,
    AppConfigDefinitionListResult,
)
from ai.backend.manager.errors.app_config import AppConfigDefinitionNotFound
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.repositories.app_config_definition.creators import (
    AppConfigDefinitionCreatorSpec,
)
from ai.backend.manager.repositories.app_config_definition.repository import (
    AppConfigDefinitionRepository,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    OffsetPagination,
    Purger,
)
from ai.backend.manager.services.app_config_definition.actions.admin_search import (
    AdminSearchAppConfigDefinitionsAction,
)
from ai.backend.manager.services.app_config_definition.actions.create import (
    CreateAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.get import (
    GetAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.actions.purge import (
    PurgeAppConfigDefinitionAction,
)
from ai.backend.manager.services.app_config_definition.service import (
    AppConfigDefinitionService,
)


class TestAppConfigDefinitionService:
    @pytest.fixture
    def definition_data(self) -> AppConfigDefinitionData:
        return AppConfigDefinitionData(
            id=AppConfigDefinitionID(uuid.uuid4()),
            config_name="theme",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigDefinitionRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> AppConfigDefinitionService:
        return AppConfigDefinitionService(repository=mock_repository)

    async def test_create(
        self,
        service: AppConfigDefinitionService,
        mock_repository: MagicMock,
        definition_data: AppConfigDefinitionData,
    ) -> None:
        mock_repository.create = AsyncMock(return_value=definition_data)
        creator = Creator(spec=AppConfigDefinitionCreatorSpec(config_name="theme"))

        result = await service.create(CreateAppConfigDefinitionAction(creator=creator))

        assert result.definition == definition_data
        mock_repository.create.assert_called_once_with(creator)

    async def test_get(
        self,
        service: AppConfigDefinitionService,
        mock_repository: MagicMock,
        definition_data: AppConfigDefinitionData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=definition_data)

        result = await service.get(GetAppConfigDefinitionAction(definition_id=definition_data.id))

        assert result.definition == definition_data
        mock_repository.get_by_id.assert_called_once_with(definition_data.id)

    async def test_get_not_found(
        self,
        service: AppConfigDefinitionService,
        mock_repository: MagicMock,
    ) -> None:
        missing_id = AppConfigDefinitionID(uuid.uuid4())
        mock_repository.get_by_id = AsyncMock(
            side_effect=AppConfigDefinitionNotFound(f"id {missing_id} not found")
        )

        with pytest.raises(AppConfigDefinitionNotFound):
            await service.get(GetAppConfigDefinitionAction(definition_id=missing_id))

    async def test_search(
        self,
        service: AppConfigDefinitionService,
        mock_repository: MagicMock,
        definition_data: AppConfigDefinitionData,
    ) -> None:
        mock_repository.admin_search = AsyncMock(
            return_value=AppConfigDefinitionListResult(
                items=[definition_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

        result = await service.admin_search(AdminSearchAppConfigDefinitionsAction(querier=querier))

        assert result.items == [definition_data]
        assert result.total_count == 1
        mock_repository.admin_search.assert_called_once_with(querier)

    async def test_purge(
        self,
        service: AppConfigDefinitionService,
        mock_repository: MagicMock,
        definition_data: AppConfigDefinitionData,
    ) -> None:
        mock_repository.purge = AsyncMock(return_value=definition_data)
        purger = Purger(row_class=AppConfigDefinitionRow, pk_value=definition_data.id)

        result = await service.purge(PurgeAppConfigDefinitionAction(purger=purger))

        assert result.definition == definition_data
        mock_repository.purge.assert_called_once_with(purger)
