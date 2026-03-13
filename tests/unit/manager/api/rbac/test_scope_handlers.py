"""
Tests for RBAC API handlers (scope-related endpoints).
Tests get_scope_types and search_scopes handlers by directly calling the
new constructor-DI based RBACHandler methods with typed parameters.
"""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.api_handlers import BodyParam, PathParam
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.dto.manager.rbac.path import SearchScopesPathParam
from ai.backend.common.dto.manager.rbac.request import SearchScopesRequest
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import ScopeData
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesActionResult,
)


def make_test_handler(mock_permission_controller: MagicMock) -> RBACHandler:
    """Create an RBACHandler with mock permission controller processors."""
    return RBACHandler(permission_controller=mock_permission_controller)


def make_test_superadmin_ctx() -> UserContext:
    """Create a UserContext for a superadmin user."""
    return UserContext(
        user_uuid=uuid4(),
        user_email="admin@test.com",
        user_domain="default",
        user_role=UserRole.SUPERADMIN,
        access_key="TESTKEY",
        is_admin=True,
        is_superadmin=True,
    )


def make_test_user_ctx() -> UserContext:
    """Create a UserContext for a regular (non-superadmin) user."""
    return UserContext(
        user_uuid=uuid4(),
        user_email="user@test.com",
        user_domain="default",
        user_role=UserRole.USER,
        access_key="USERKEY",
        is_admin=False,
        is_superadmin=False,
    )


class TestGetScopeTypesHandler:
    """Tests for get_scope_types handler."""

    # Constants
    EXPECTED_SCOPE_TYPES_COUNT = len(ScopeType)

    @pytest.fixture
    def mock_permission_controller(self) -> MagicMock:
        """Create mock permission controller processors."""
        pc = MagicMock()
        pc.get_scope_types = MagicMock()
        pc.get_scope_types.wait_for_complete = AsyncMock()
        return pc

    async def test_get_scope_types_returns_scope_types(
        self,
        mock_permission_controller: MagicMock,
    ) -> None:
        """Test get_scope_types returns all scope types for superadmin."""
        handler = make_test_handler(mock_permission_controller)
        ctx = make_test_superadmin_ctx()
        action_result = GetScopeTypesActionResult(scope_types=list(ScopeType))
        mock_permission_controller.get_scope_types.wait_for_complete.return_value = action_result

        response = await handler.get_scope_types(ctx=ctx)

        assert response.status_code == HTTPStatus.OK
        response_json = response.to_json
        assert isinstance(response_json, dict)
        assert "items" in response_json
        assert len(response_json["items"]) == self.EXPECTED_SCOPE_TYPES_COUNT

    async def test_get_scope_types_rejects_non_superadmin(
        self,
        mock_permission_controller: MagicMock,
    ) -> None:
        """Test get_scope_types rejects non-superadmin users."""
        handler = make_test_handler(mock_permission_controller)
        ctx = make_test_user_ctx()

        with pytest.raises(NotEnoughPermission):
            await handler.get_scope_types(ctx=ctx)


class TestSearchScopesHandler:
    """Tests for search_scopes handler."""

    # Constants
    TEST_DOMAIN_NAME = "test-domain"
    TEST_SCOPE_TYPE = ScopeType.DOMAIN
    DEFAULT_LIMIT = 10
    DEFAULT_OFFSET = 0
    PAGINATION_LIMIT = 5
    PAGINATION_TOTAL = 15
    PAGINATION_ITEMS_COUNT = 5

    @pytest.fixture
    def mock_permission_controller(self) -> MagicMock:
        """Create mock permission controller processors."""
        pc = MagicMock()
        pc.search_scopes = MagicMock()
        pc.search_scopes.wait_for_complete = AsyncMock()
        return pc

    @staticmethod
    def _make_path_param(scope_type: ScopeType) -> PathParam[SearchScopesPathParam]:
        param = MagicMock(spec=PathParam)
        param.parsed = SearchScopesPathParam(scope_type=scope_type)
        return param

    @staticmethod
    def _make_body_param(*, limit: int = 10, offset: int = 0) -> BodyParam[SearchScopesRequest]:
        param = MagicMock(spec=BodyParam)
        param.parsed = SearchScopesRequest(
            filter=None,
            order=None,
            limit=limit,
            offset=offset,
        )
        return param

    @pytest.fixture
    def single_scope_result(self) -> SearchScopesActionResult:
        """Create action result with single scope item."""
        return SearchScopesActionResult(
            result=SearchResult(
                items=[
                    ScopeData(
                        id=ScopeId(scope_type=self.TEST_SCOPE_TYPE, scope_id=self.TEST_DOMAIN_NAME),
                        name=self.TEST_DOMAIN_NAME,
                    ),
                ],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            ),
        )

    @pytest.fixture
    def paginated_scope_result(self) -> SearchScopesActionResult:
        """Create action result with pagination."""
        return SearchScopesActionResult(
            result=SearchResult(
                items=[
                    ScopeData(
                        id=ScopeId(scope_type=self.TEST_SCOPE_TYPE, scope_id=f"domain-{i}"),
                        name=f"domain-{i}",
                    )
                    for i in range(self.PAGINATION_ITEMS_COUNT)
                ],
                total_count=self.PAGINATION_TOTAL,
                has_next_page=True,
                has_previous_page=False,
            ),
        )

    @pytest.fixture
    def empty_scope_result(self) -> SearchScopesActionResult:
        """Create empty action result."""
        return SearchScopesActionResult(
            result=SearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            ),
        )

    async def test_search_scopes_returns_results(
        self,
        mock_permission_controller: MagicMock,
        single_scope_result: SearchScopesActionResult,
    ) -> None:
        """Test search_scopes returns scope results for superadmin."""
        handler = make_test_handler(mock_permission_controller)
        ctx = make_test_superadmin_ctx()
        mock_permission_controller.search_scopes.wait_for_complete.return_value = (
            single_scope_result
        )
        path = self._make_path_param(self.TEST_SCOPE_TYPE)
        body = self._make_body_param()

        response = await handler.search_scopes(path=path, body=body, ctx=ctx)

        assert response.status_code == HTTPStatus.OK
        response_json = response.to_json
        assert isinstance(response_json, dict)
        assert "items" in response_json
        assert len(response_json["items"]) == len(single_scope_result.result.items)
        assert response_json["items"][0]["scope_type"] == self.TEST_SCOPE_TYPE.value
        assert response_json["items"][0]["name"] == self.TEST_DOMAIN_NAME

    async def test_search_scopes_with_pagination(
        self,
        mock_permission_controller: MagicMock,
        paginated_scope_result: SearchScopesActionResult,
    ) -> None:
        """Test search_scopes returns correct pagination info."""
        handler = make_test_handler(mock_permission_controller)
        ctx = make_test_superadmin_ctx()
        mock_permission_controller.search_scopes.wait_for_complete.return_value = (
            paginated_scope_result
        )
        path = self._make_path_param(self.TEST_SCOPE_TYPE)
        body = self._make_body_param(limit=self.PAGINATION_LIMIT, offset=self.DEFAULT_OFFSET)

        response = await handler.search_scopes(path=path, body=body, ctx=ctx)

        response_json = response.to_json
        assert isinstance(response_json, dict)
        pagination = response_json["pagination"]
        assert pagination["total"] == self.PAGINATION_TOTAL
        assert pagination["offset"] == self.DEFAULT_OFFSET
        assert pagination["limit"] == self.PAGINATION_LIMIT

    async def test_search_scopes_calls_processor_with_action(
        self,
        mock_permission_controller: MagicMock,
        empty_scope_result: SearchScopesActionResult,
    ) -> None:
        """Test search_scopes calls processor with correct action."""
        handler = make_test_handler(mock_permission_controller)
        ctx = make_test_superadmin_ctx()
        mock_permission_controller.search_scopes.wait_for_complete.return_value = empty_scope_result
        path = self._make_path_param(self.TEST_SCOPE_TYPE)
        body = self._make_body_param()

        await handler.search_scopes(path=path, body=body, ctx=ctx)

        mock_permission_controller.search_scopes.wait_for_complete.assert_called_once()
        call_args = mock_permission_controller.search_scopes.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.scope_type == self.TEST_SCOPE_TYPE

    async def test_search_scopes_rejects_non_superadmin(
        self,
        mock_permission_controller: MagicMock,
    ) -> None:
        """Test search_scopes rejects non-superadmin users."""
        handler = make_test_handler(mock_permission_controller)
        ctx = make_test_user_ctx()
        path = self._make_path_param(self.TEST_SCOPE_TYPE)
        body = self._make_body_param()

        with pytest.raises(NotEnoughPermission):
            await handler.search_scopes(path=path, body=body, ctx=ctx)
