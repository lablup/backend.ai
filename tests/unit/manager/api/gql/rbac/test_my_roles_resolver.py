"""Tests for my_roles GraphQL resolver."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.gql.rbac.resolver import role as role_resolver
from ai.backend.manager.api.gql.rbac.types import RoleConnection
from ai.backend.manager.repositories.permission_controller.options import RoleConditions


class TestMyRoles:
    """Tests for my_roles resolver."""

    @pytest.fixture
    def user_id(self) -> UUID:
        return UUID("11111111-2222-3333-4444-555555555555")

    @pytest.fixture
    def user_data(self, user_id: UUID) -> UserData:
        return UserData(
            user_id=user_id,
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.mark.asyncio
    async def test_calls_fetch_roles_with_user_condition(
        self,
        user_data: UserData,
        user_id: UUID,
    ) -> None:
        """Should call fetch_roles with base_conditions filtering by user_id."""
        info = MagicMock()
        mock_connection = MagicMock(spec=RoleConnection)

        with (
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
                return_value=user_data,
            ),
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.fetch_roles",
                new_callable=AsyncMock,
                return_value=mock_connection,
            ) as mock_fetch,
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

            assert result == mock_connection
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            assert call_args[0][0] == info
            assert call_args.kwargs["first"] == 10
            assert call_args.kwargs["filter"] is None
            assert call_args.kwargs["order_by"] is None

            base_conditions = call_args.kwargs["base_conditions"]
            assert len(base_conditions) == 1

    @pytest.mark.asyncio
    async def test_raises_unauthorized_when_not_authenticated(self) -> None:
        """Should raise HTTPUnauthorized when no user is authenticated."""
        info = MagicMock()

        with patch(
            "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
            return_value=None,
        ):
            resolver_fn = role_resolver.my_roles.base_resolver
            with pytest.raises(web.HTTPUnauthorized):
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

    @pytest.mark.asyncio
    async def test_passes_pagination_params(
        self,
        user_data: UserData,
    ) -> None:
        """Should pass all pagination parameters to fetch_roles."""
        info = MagicMock()
        mock_connection = MagicMock(spec=RoleConnection)

        with (
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
                return_value=user_data,
            ),
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.fetch_roles",
                new_callable=AsyncMock,
                return_value=mock_connection,
            ) as mock_fetch,
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

            call_kwargs = mock_fetch.call_args.kwargs
            assert call_kwargs["before"] == "before_cursor"
            assert call_kwargs["after"] == "after_cursor"
            assert call_kwargs["first"] == 5
            assert call_kwargs["last"] == 3
            assert call_kwargs["limit"] == 20
            assert call_kwargs["offset"] == 10


class TestRoleConditionsByAssignedUserId:
    """Tests for RoleConditions.by_assigned_user_id."""

    def test_returns_callable(self) -> None:
        """Should return a callable query condition."""
        user_id = UUID("11111111-2222-3333-4444-555555555555")
        condition = RoleConditions.by_assigned_user_id(user_id)
        assert callable(condition)
