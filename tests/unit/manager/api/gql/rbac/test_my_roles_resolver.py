"""Tests for my_roles GraphQL resolver."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.gql.rbac.resolver import role as role_resolver
from ai.backend.manager.api.gql.rbac.types import RoleAssignmentConnection
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.errors.auth import InsufficientPrivilege


class TestMyRoles:
    """Tests for my_roles resolver."""

    @pytest.fixture
    def user_data(self) -> UserData:
        return UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    async def test_calls_adapter_with_user_condition(
        self,
        user_data: UserData,
    ) -> None:
        """Should call adapter with base_conditions filtering by user_id."""
        mock_search = AsyncMock(
            return_value=SearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        info = MagicMock()
        info.context.adapters.rbac.admin_search_role_assignments_gql = mock_search

        with patch(
            "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
            return_value=user_data,
        ):
            resolver_fn = role_resolver.my_roles.base_resolver
            result = await resolver_fn(
                info,
                None,  # filter
                None,  # order_by
                None,  # before
                None,  # after
                10,  # first
                None,  # last
                None,  # limit
                None,  # offset
            )

        assert isinstance(result, RoleAssignmentConnection)
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[0][0].first == 10

        base_conditions = call_args.kwargs["base_conditions"]
        assert len(base_conditions) == 1

    async def test_raises_insufficient_privilege_when_not_authenticated(self) -> None:
        """Should raise InsufficientPrivilege when no user is authenticated."""
        info = MagicMock()

        with patch(
            "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
            return_value=None,
        ):
            resolver_fn = role_resolver.my_roles.base_resolver
            with pytest.raises(InsufficientPrivilege):
                await resolver_fn(
                    info,
                    None,  # filter
                    None,  # order_by
                    None,  # before
                    None,  # after
                    None,  # first
                    None,  # last
                    None,  # limit
                    None,  # offset
                )

    async def test_passes_pagination_params(
        self,
        user_data: UserData,
    ) -> None:
        """Should pass all pagination parameters to adapter."""
        mock_search = AsyncMock(
            return_value=SearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        info = MagicMock()
        info.context.adapters.rbac.admin_search_role_assignments_gql = mock_search

        with patch(
            "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
            return_value=user_data,
        ):
            resolver_fn = role_resolver.my_roles.base_resolver
            await resolver_fn(
                info,
                None,  # filter
                None,  # order_by
                "before_cursor",  # before
                "after_cursor",  # after
                5,  # first
                3,  # last
                20,  # limit
                10,  # offset
            )

        input_dto = mock_search.call_args[0][0]
        assert input_dto.before == "before_cursor"
        assert input_dto.after == "after_cursor"
        assert input_dto.first == 5
        assert input_dto.last == 3
        assert input_dto.limit == 20
        assert input_dto.offset == 10
