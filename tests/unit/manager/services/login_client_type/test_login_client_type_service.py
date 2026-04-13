"""Tests for LoginClientTypeService and LoginClientTypeAdminService.

Tests the service layer with mocked repositories.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.data.login_client_type.types import (
    LoginClientTypeData,
    LoginClientTypeSearchResult,
)
from ai.backend.manager.errors.auth import LoginClientTypeConflict, LoginClientTypeNotFound
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.login_client_type.admin_repository import (
    LoginClientTypeAdminRepository,
)
from ai.backend.manager.repositories.login_client_type.repository import (
    LoginClientTypeRepository,
)
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.delete import (
    DeleteLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.search import (
    SearchLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.admin_service import (
    LoginClientTypeAdminService,
)
from ai.backend.manager.services.login_client_type.service import LoginClientTypeService


class TestLoginClientTypeService:
    @pytest.fixture
    def login_client_type_data(self) -> LoginClientTypeData:
        return LoginClientTypeData(
            id=uuid4(),
            name="webui",
            description="Backend.AI web console.",
            created_at=datetime.now(UTC),
            modified_at=datetime.now(UTC),
        )

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=LoginClientTypeRepository)

    @pytest.fixture
    def service(self, mock_repository: MagicMock) -> LoginClientTypeService:
        return LoginClientTypeService(repository=mock_repository)

    async def test_get(
        self,
        service: LoginClientTypeService,
        mock_repository: MagicMock,
        login_client_type_data: LoginClientTypeData,
    ) -> None:
        mock_repository.get_by_id = AsyncMock(return_value=login_client_type_data)

        action = GetLoginClientTypeAction(id=login_client_type_data.id)
        result = await service.get(action)

        assert result.login_client_type == login_client_type_data
        mock_repository.get_by_id.assert_called_once_with(login_client_type_data.id)

    async def test_get_not_found(
        self,
        service: LoginClientTypeService,
        mock_repository: MagicMock,
    ) -> None:
        login_client_type_id = uuid4()
        mock_repository.get_by_id = AsyncMock(
            side_effect=LoginClientTypeNotFound(extra_msg=f"id {login_client_type_id} not found")
        )

        action = GetLoginClientTypeAction(id=login_client_type_id)

        with pytest.raises(LoginClientTypeNotFound):
            await service.get(action)

    async def test_search(
        self,
        service: LoginClientTypeService,
        mock_repository: MagicMock,
        login_client_type_data: LoginClientTypeData,
    ) -> None:
        items = [login_client_type_data]
        mock_repository.search = AsyncMock(
            return_value=LoginClientTypeSearchResult(
                items=items,
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchLoginClientTypesAction(querier=querier)
        result = await service.search(action)

        assert result.items == items
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search.assert_called_once_with(querier=querier)

    async def test_search_empty(
        self,
        service: LoginClientTypeService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.search = AsyncMock(
            return_value=LoginClientTypeSearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchLoginClientTypesAction(querier=querier)
        result = await service.search(action)

        assert result.items == []
        assert result.total_count == 0

    async def test_search_with_pagination(
        self,
        service: LoginClientTypeService,
        mock_repository: MagicMock,
        login_client_type_data: LoginClientTypeData,
    ) -> None:
        items = [login_client_type_data]
        mock_repository.search = AsyncMock(
            return_value=LoginClientTypeSearchResult(
                items=items,
                total_count=3,
                has_next_page=True,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchLoginClientTypesAction(querier=querier)
        result = await service.search(action)

        assert len(result.items) == 1
        assert result.total_count == 3
        assert result.has_next_page is True
        assert result.has_previous_page is False


class TestLoginClientTypeAdminService:
    @pytest.fixture
    def login_client_type_data(self) -> LoginClientTypeData:
        return LoginClientTypeData(
            id=uuid4(),
            name="webui",
            description="Backend.AI web console.",
            created_at=datetime.now(UTC),
            modified_at=datetime.now(UTC),
        )

    @pytest.fixture
    def mock_admin_repository(self) -> MagicMock:
        return MagicMock(spec=LoginClientTypeAdminRepository)

    @pytest.fixture
    def admin_service(self, mock_admin_repository: MagicMock) -> LoginClientTypeAdminService:
        return LoginClientTypeAdminService(admin_repository=mock_admin_repository)

    async def test_create(
        self,
        admin_service: LoginClientTypeAdminService,
        mock_admin_repository: MagicMock,
        login_client_type_data: LoginClientTypeData,
    ) -> None:
        mock_admin_repository.create = AsyncMock(return_value=login_client_type_data)

        creator = MagicMock(spec=Creator)
        action = CreateLoginClientTypeAction(creator=creator)
        result = await admin_service.create(action)

        assert result.login_client_type == login_client_type_data
        mock_admin_repository.create.assert_called_once_with(creator)

    async def test_create_duplicate_name_raises(
        self,
        admin_service: LoginClientTypeAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        mock_admin_repository.create = AsyncMock(
            side_effect=LoginClientTypeConflict("already exists")
        )

        creator = MagicMock(spec=Creator)
        action = CreateLoginClientTypeAction(creator=creator)

        with pytest.raises(LoginClientTypeConflict):
            await admin_service.create(action)

    async def test_update(
        self,
        admin_service: LoginClientTypeAdminService,
        mock_admin_repository: MagicMock,
        login_client_type_data: LoginClientTypeData,
    ) -> None:
        mock_admin_repository.update = AsyncMock(return_value=login_client_type_data)

        updater = MagicMock(spec=Updater)
        action = UpdateLoginClientTypeAction(updater=updater)
        result = await admin_service.update(action)

        assert result.login_client_type == login_client_type_data
        mock_admin_repository.update.assert_called_once_with(updater)

    async def test_update_not_found(
        self,
        admin_service: LoginClientTypeAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        mock_admin_repository.update = AsyncMock(
            side_effect=LoginClientTypeNotFound(extra_msg="not found")
        )

        updater = MagicMock(spec=Updater)
        action = UpdateLoginClientTypeAction(updater=updater)

        with pytest.raises(LoginClientTypeNotFound):
            await admin_service.update(action)

    async def test_delete(
        self,
        admin_service: LoginClientTypeAdminService,
        mock_admin_repository: MagicMock,
        login_client_type_data: LoginClientTypeData,
    ) -> None:
        mock_admin_repository.delete = AsyncMock(return_value=login_client_type_data)

        action = DeleteLoginClientTypeAction(id=login_client_type_data.id)
        result = await admin_service.delete(action)

        assert result.login_client_type == login_client_type_data
        mock_admin_repository.delete.assert_called_once_with(login_client_type_data.id)

    async def test_delete_not_found(
        self,
        admin_service: LoginClientTypeAdminService,
        mock_admin_repository: MagicMock,
    ) -> None:
        login_client_type_id = uuid4()
        mock_admin_repository.delete = AsyncMock(
            side_effect=LoginClientTypeNotFound(extra_msg=f"id {login_client_type_id} not found")
        )

        action = DeleteLoginClientTypeAction(id=login_client_type_id)

        with pytest.raises(LoginClientTypeNotFound):
            await admin_service.delete(action)
