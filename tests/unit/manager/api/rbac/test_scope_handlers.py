"""
Tests for RBAC API handlers (scope-related endpoints).
Tests get_scope_types and search_scopes handlers by calling the decorated handler
with properly mocked requests, following the pattern in test_resource.py.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import cast
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
from uuid import uuid4

import pytest
from aiohttp import web

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.rbac.handler import RBACAPIHandler
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import ScopeData
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    GetScopeTypesActionResult,
)
from ai.backend.manager.services.permission_contoller.actions.search_scopes import (
    SearchScopesActionResult,
)


class TestGetScopeTypesHandler:
    """Tests for get_scope_types handler."""

    # Constants
    EXPECTED_SCOPE_TYPES_COUNT = len(ScopeType)

    @pytest.fixture
    def handler(self) -> RBACAPIHandler:
        """Create RBACAPIHandler instance."""
        return RBACAPIHandler()

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        """Create mock processors with permission_controller."""
        processors = MagicMock()
        processors.permission_controller.get_scope_types = MagicMock()
        processors.permission_controller.get_scope_types.wait_for_complete = AsyncMock()
        return processors

    @pytest.fixture
    def mock_processors_ctx(self, mock_processors: MagicMock) -> MagicMock:
        """Create mock ProcessorsCtx that bypasses Pydantic validation."""
        ctx = MagicMock()
        ctx.processors = mock_processors
        return ctx

    @pytest.fixture
    def mock_root_ctx(self, mock_processors: MagicMock) -> MagicMock:
        """RootContext mock with processors."""
        root_ctx = MagicMock()
        root_ctx.processors = mock_processors
        return root_ctx

    @pytest.fixture
    def superadmin_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock request for superadmin user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        return req

    @pytest.fixture
    def authorized_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock request for authorized (non-superadmin) user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": False,
        }.get(k, default)
        return req

    @pytest.fixture
    def unauthorized_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock request for unauthorized user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": False,
            "is_superadmin": False,
        }.get(k, default)
        return req

    @pytest.fixture
    def superadmin_user(self) -> UserData:
        """Create superadmin user data."""
        return UserData(
            user_id=uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=True,
            role=UserRole.SUPERADMIN,
            domain_name="default",
        )

    @pytest.fixture
    def regular_user(self) -> UserData:
        """Create regular (non-superadmin) user data."""
        return UserData(
            user_id=uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.mark.asyncio
    async def test_get_scope_types_returns_scope_types(
        self,
        handler: RBACAPIHandler,
        superadmin_request: MagicMock,
        mock_processors: MagicMock,
        mock_processors_ctx: MagicMock,
        superadmin_user: UserData,
    ) -> None:
        """Test get_scope_types returns all scope types for superadmin."""
        action_result = GetScopeTypesActionResult(scope_types=list(ScopeType))
        mock_processors.permission_controller.get_scope_types.wait_for_complete.return_value = (
            action_result
        )

        with (
            with_user(superadmin_user),
            patch(
                "ai.backend.manager.dto.context.ProcessorsCtx.from_request",
                new_callable=AsyncMock,
                return_value=mock_processors_ctx,
            ),
        ):
            response = await handler.get_scope_types(superadmin_request)

        assert response.status == HTTPStatus.OK
        response_body = cast(web.Response, response).body
        assert response_body is not None
        response_data = json.loads(cast(bytes, response_body))
        assert "items" in response_data
        assert len(response_data["items"]) == self.EXPECTED_SCOPE_TYPES_COUNT

    @pytest.mark.asyncio
    async def test_get_scope_types_rejects_non_superadmin(
        self,
        handler: RBACAPIHandler,
        authorized_request: MagicMock,
        mock_processors_ctx: MagicMock,
        regular_user: UserData,
    ) -> None:
        """Test get_scope_types rejects non-superadmin users."""
        with (
            with_user(regular_user),
            patch(
                "ai.backend.manager.dto.context.ProcessorsCtx.from_request",
                new_callable=AsyncMock,
                return_value=mock_processors_ctx,
            ),
        ):
            with pytest.raises(Exception):
                await handler.get_scope_types(authorized_request)

    @pytest.mark.asyncio
    async def test_get_scope_types_rejects_unauthenticated(
        self,
        handler: RBACAPIHandler,
        unauthorized_request: MagicMock,
    ) -> None:
        """Test get_scope_types rejects unauthenticated requests."""
        with pytest.raises(AuthorizationFailed):
            await handler.get_scope_types(unauthorized_request)


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
    def handler(self) -> RBACAPIHandler:
        """Create RBACAPIHandler instance."""
        return RBACAPIHandler()

    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        """Create mock processors with permission_controller."""
        processors = MagicMock()
        processors.permission_controller.search_scopes = MagicMock()
        processors.permission_controller.search_scopes.wait_for_complete = AsyncMock()
        return processors

    @pytest.fixture
    def mock_processors_ctx(self, mock_processors: MagicMock) -> MagicMock:
        """Create mock ProcessorsCtx that bypasses Pydantic validation."""
        ctx = MagicMock()
        ctx.processors = mock_processors
        return ctx

    @pytest.fixture
    def mock_root_ctx(self, mock_processors: MagicMock) -> MagicMock:
        """RootContext mock with processors."""
        root_ctx = MagicMock()
        root_ctx.processors = mock_processors
        return root_ctx

    @pytest.fixture
    def superadmin_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for superadmin user with body parsing support."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        req.match_info = {"scope_type": self.TEST_SCOPE_TYPE.value}
        req.json = AsyncMock(
            return_value={
                "filter": None,
                "order": None,
                "limit": self.DEFAULT_LIMIT,
                "offset": self.DEFAULT_OFFSET,
            }
        )
        return req

    @pytest.fixture
    def authorized_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock request for authorized (non-superadmin) user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": False,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        req.match_info = {"scope_type": self.TEST_SCOPE_TYPE.value}
        req.json = AsyncMock(
            return_value={"limit": self.DEFAULT_LIMIT, "offset": self.DEFAULT_OFFSET}
        )
        return req

    @pytest.fixture
    def unauthorized_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock request for unauthorized user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": False,
            "is_superadmin": False,
        }.get(k, default)
        return req

    @pytest.fixture
    def superadmin_user(self) -> UserData:
        """Create superadmin user data."""
        return UserData(
            user_id=uuid4(),
            is_authorized=True,
            is_admin=True,
            is_superadmin=True,
            role=UserRole.SUPERADMIN,
            domain_name="default",
        )

    @pytest.fixture
    def regular_user(self) -> UserData:
        """Create regular (non-superadmin) user data."""
        return UserData(
            user_id=uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.fixture
    def single_scope_result(self) -> SearchScopesActionResult:
        """Create action result with single scope item."""
        return SearchScopesActionResult(
            items=[
                ScopeData(
                    id=ScopeId(scope_type=self.TEST_SCOPE_TYPE, scope_id=self.TEST_DOMAIN_NAME),
                    name=self.TEST_DOMAIN_NAME,
                ),
            ],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

    @pytest.fixture
    def paginated_scope_result(self) -> SearchScopesActionResult:
        """Create action result with pagination."""
        return SearchScopesActionResult(
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
        )

    @pytest.fixture
    def empty_scope_result(self) -> SearchScopesActionResult:
        """Create empty action result."""
        return SearchScopesActionResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )

    @pytest.mark.asyncio
    async def test_search_scopes_returns_results(
        self,
        handler: RBACAPIHandler,
        superadmin_request: MagicMock,
        mock_processors: MagicMock,
        mock_processors_ctx: MagicMock,
        superadmin_user: UserData,
        single_scope_result: SearchScopesActionResult,
    ) -> None:
        """Test search_scopes returns scope results for superadmin."""
        mock_processors.permission_controller.search_scopes.wait_for_complete.return_value = (
            single_scope_result
        )

        with (
            with_user(superadmin_user),
            patch(
                "ai.backend.manager.dto.context.ProcessorsCtx.from_request",
                new_callable=AsyncMock,
                return_value=mock_processors_ctx,
            ),
        ):
            response = await handler.search_scopes(superadmin_request)

        assert response.status == HTTPStatus.OK
        response_body = cast(web.Response, response).body
        assert response_body is not None
        response_data = json.loads(cast(bytes, response_body))
        assert "items" in response_data
        assert "pagination" in response_data
        assert len(response_data["items"]) == len(single_scope_result.items)
        assert response_data["items"][0]["scope_type"] == self.TEST_SCOPE_TYPE.value
        assert response_data["items"][0]["name"] == self.TEST_DOMAIN_NAME

    @pytest.mark.asyncio
    async def test_search_scopes_with_pagination(
        self,
        handler: RBACAPIHandler,
        superadmin_request: MagicMock,
        mock_processors: MagicMock,
        mock_processors_ctx: MagicMock,
        superadmin_user: UserData,
        paginated_scope_result: SearchScopesActionResult,
    ) -> None:
        """Test search_scopes returns correct pagination info."""
        mock_processors.permission_controller.search_scopes.wait_for_complete.return_value = (
            paginated_scope_result
        )

        superadmin_request.json = AsyncMock(
            return_value={
                "filter": None,
                "order": None,
                "limit": self.PAGINATION_LIMIT,
                "offset": self.DEFAULT_OFFSET,
            }
        )

        with (
            with_user(superadmin_user),
            patch(
                "ai.backend.manager.dto.context.ProcessorsCtx.from_request",
                new_callable=AsyncMock,
                return_value=mock_processors_ctx,
            ),
        ):
            response = await handler.search_scopes(superadmin_request)

        response_body = cast(web.Response, response).body
        response_data = json.loads(cast(bytes, response_body))
        assert response_data is not None
        assert response_data["pagination"]["total"] == self.PAGINATION_TOTAL
        assert response_data["pagination"]["offset"] == self.DEFAULT_OFFSET
        assert response_data["pagination"]["limit"] == self.PAGINATION_LIMIT

    @pytest.mark.asyncio
    async def test_search_scopes_calls_processor_with_action(
        self,
        handler: RBACAPIHandler,
        superadmin_request: MagicMock,
        mock_processors: MagicMock,
        mock_processors_ctx: MagicMock,
        superadmin_user: UserData,
        empty_scope_result: SearchScopesActionResult,
    ) -> None:
        """Test search_scopes calls processor with correct action."""
        mock_processors.permission_controller.search_scopes.wait_for_complete.return_value = (
            empty_scope_result
        )

        with (
            with_user(superadmin_user),
            patch(
                "ai.backend.manager.dto.context.ProcessorsCtx.from_request",
                new_callable=AsyncMock,
                return_value=mock_processors_ctx,
            ),
        ):
            await handler.search_scopes(superadmin_request)

        mock_processors.permission_controller.search_scopes.wait_for_complete.assert_called_once()

        call_args = mock_processors.permission_controller.search_scopes.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.scope_type == self.TEST_SCOPE_TYPE

    @pytest.mark.asyncio
    async def test_search_scopes_rejects_non_superadmin(
        self,
        handler: RBACAPIHandler,
        authorized_request: MagicMock,
        mock_processors_ctx: MagicMock,
        regular_user: UserData,
    ) -> None:
        """Test search_scopes rejects non-superadmin users."""
        with (
            with_user(regular_user),
            patch(
                "ai.backend.manager.dto.context.ProcessorsCtx.from_request",
                new_callable=AsyncMock,
                return_value=mock_processors_ctx,
            ),
        ):
            with pytest.raises(Exception):
                await handler.search_scopes(authorized_request)

    @pytest.mark.asyncio
    async def test_search_scopes_rejects_unauthenticated(
        self,
        handler: RBACAPIHandler,
        unauthorized_request: MagicMock,
    ) -> None:
        """Test search_scopes rejects unauthenticated requests."""
        with pytest.raises(AuthorizationFailed):
            await handler.search_scopes(unauthorized_request)
