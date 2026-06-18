"""Tests for AppConfigAllowListService with a mocked repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
    AppConfigAllowListSearchResult,
    AppConfigScopeType,
)
from ai.backend.manager.errors.app_config import AppConfigAllowListNotFound
from ai.backend.manager.repositories.app_config_allow_list.creators import (
    AppConfigAllowListCreatorSpec,
)
from ai.backend.manager.repositories.app_config_allow_list.repository import (
    AppConfigAllowListRepository,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.manager.services.app_config_allow_list.actions.create import (
    CreateAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.get import (
    GetAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.purge import (
    PurgeAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.actions.search import (
    SearchAppConfigAllowListAction,
)
from ai.backend.manager.services.app_config_allow_list.service import (
    AppConfigAllowListService,
)


class TestAppConfigAllowListService:
    @pytest.fixture
    def allow_list_data(self) -> AppConfigAllowListData:
        return AppConfigAllowListData(
            id=AppConfigAllowListID(uuid.uuid4()),
            config_name="theme",
            scope_type=AppConfigScopeType.USER,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AppConfigAllowListRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> AppConfigAllowListService:
        return AppConfigAllowListService(repository=mock_repository)

    async def test_create(
        self,
        service: AppConfigAllowListService,
        mock_repository: MagicMock,
        allow_list_data: AppConfigAllowListData,
    ) -> None:
        mock_repository.create = AsyncMock(return_value=allow_list_data)
        creator = Creator(
            spec=AppConfigAllowListCreatorSpec(
                config_name="theme", scope_type=AppConfigScopeType.USER
            )
        )

        result = await service.create(CreateAppConfigAllowListAction(creator=creator))

        assert result.allow_list == allow_list_data
        mock_repository.create.assert_called_once_with(creator)

    async def test_get(
        self,
        service: AppConfigAllowListService,
        mock_repository: MagicMock,
        allow_list_data: AppConfigAllowListData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=allow_list_data)

        result = await service.get(GetAppConfigAllowListAction(allow_list_id=allow_list_data.id))

        assert result.allow_list == allow_list_data
        mock_repository.get_by_id.assert_called_once_with(allow_list_data.id)

    async def test_get_not_found(
        self,
        service: AppConfigAllowListService,
        mock_repository: MagicMock,
    ) -> None:
        missing_id = AppConfigAllowListID(uuid.uuid4())
        mock_repository.get_by_id = AsyncMock(
            side_effect=AppConfigAllowListNotFound(f"id {missing_id} not found")
        )

        with pytest.raises(AppConfigAllowListNotFound):
            await service.get(GetAppConfigAllowListAction(allow_list_id=missing_id))

    async def test_search(
        self,
        service: AppConfigAllowListService,
        mock_repository: MagicMock,
        allow_list_data: AppConfigAllowListData,
    ) -> None:
        mock_repository.search = AsyncMock(
            return_value=AppConfigAllowListSearchResult(
                items=[allow_list_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))

        result = await service.search(SearchAppConfigAllowListAction(querier=querier))

        assert result.data == [allow_list_data]
        assert result.total_count == 1
        mock_repository.search.assert_called_once_with(querier)

    async def test_purge(
        self,
        service: AppConfigAllowListService,
        mock_repository: MagicMock,
        allow_list_data: AppConfigAllowListData,
    ) -> None:
        mock_repository.purge = AsyncMock(return_value=allow_list_data)

        result = await service.purge(
            PurgeAppConfigAllowListAction(allow_list_id=allow_list_data.id)
        )

        assert result.allow_list == allow_list_data
        mock_repository.purge.assert_called_once_with(allow_list_data.id)
