"""
Tests for PermissionControllerService scope search functionality.
Uses mocks for repository layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import ScopeData, ScopeListResult
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesAction,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesAction,
)
from ai.backend.manager.services.permission_contoller.service import (
    PermissionControllerService,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.permission_controller.repository import (
        PermissionControllerRepository,
    )


class TestGetScopeTypes:
    """Tests for get_scope_types service method."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create a mock repository."""
        return MagicMock()

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        """Create service with mocked repository."""
        return PermissionControllerService(
            repository=mock_repository,
            group_repository=MagicMock(),
            rbac_action_registry=[],
        )

    async def test_get_scope_types_returns_all_scope_types(
        self,
        service: PermissionControllerService,
    ) -> None:
        """Test get_scope_types returns all ScopeType enum values."""
        action = GetScopeTypesAction()

        result = await service.get_scope_types(action)

        expected_types = list(RBACElementType)
        assert len(result.element_types) == len(expected_types)
        for scope_type in expected_types:
            assert scope_type in result.element_types


class TestSearchScopes:
    """Tests for search_scopes service method."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create a mock repository with search_scopes method."""
        repository = MagicMock()
        repository.search_scopes = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        """Create service with mocked repository."""
        return PermissionControllerService(
            repository=mock_repository,
            group_repository=MagicMock(),
            rbac_action_registry=[],
        )

    async def test_search_scopes_calls_repository(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        """Test search_scopes delegates to repository."""
        domain_name = "test-domain"
        total_count = 1
        limit = 10
        offset = 0
        mock_result = ScopeListResult(
            items=[
                ScopeData(
                    id=ScopeId(scope_type=ScopeType.DOMAIN, scope_id=domain_name),
                    name=domain_name,
                )
            ],
            total_count=total_count,
            has_next_page=False,
            has_previous_page=False,
        )
        mock_repository.search_scopes.return_value = mock_result

        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action = SearchScopesAction(element_type=RBACElementType.DOMAIN, querier=querier)

        result = await service.search_scopes(action)

        mock_repository.search_scopes.assert_called_once_with(RBACElementType.DOMAIN, querier)
        assert result.result.total_count == total_count
        assert len(result.result.items) == total_count
        assert result.result.items[0].id.scope_type == ScopeType.DOMAIN

    async def test_search_scopes_returns_action_result(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        """Test search_scopes returns properly formatted SearchScopesActionResult."""
        project_id_1 = "project-1"
        project_id_2 = "project-2"
        project_name_1 = "project-alpha"
        project_name_2 = "project-beta"
        total_count = 10
        items_count = 2
        limit = 2
        offset = 0
        mock_result = ScopeListResult(
            items=[
                ScopeData(
                    id=ScopeId(scope_type=ScopeType.PROJECT, scope_id=project_id_1),
                    name=project_name_1,
                ),
                ScopeData(
                    id=ScopeId(scope_type=ScopeType.PROJECT, scope_id=project_id_2),
                    name=project_name_2,
                ),
            ],
            total_count=total_count,
            has_next_page=True,
            has_previous_page=False,
        )
        mock_repository.search_scopes.return_value = mock_result

        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=limit, offset=offset),
        )
        action = SearchScopesAction(element_type=RBACElementType.PROJECT, querier=querier)

        result = await service.search_scopes(action)

        assert result.result.total_count == total_count
        assert len(result.result.items) == items_count
        assert result.result.has_next_page is True
        assert result.result.has_previous_page is False
