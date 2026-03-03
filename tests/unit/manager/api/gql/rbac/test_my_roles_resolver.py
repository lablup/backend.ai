"""Tests for my_roles GraphQL resolver."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.gql.rbac.resolver import role as role_resolver
from ai.backend.manager.api.gql.rbac.types import RoleAssignmentConnection
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

    async def test_calls_fetch_role_assignments_with_user_condition(
        self,
        user_data: UserData,
    ) -> None:
        """Should call fetch_role_assignments with base_conditions filtering by user_id."""
        info = MagicMock()
        mock_connection = MagicMock(spec=RoleAssignmentConnection)

        with (
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
                return_value=user_data,
            ),
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.fetch_role_assignments",
                new_callable=AsyncMock,
                return_value=mock_connection,
            ) as mock_fetch,
        ):
            resolver_fn = role_resolver.my_roles.base_resolver
            result = await resolver_fn(
                info,
                None,  # filter
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
        """Should pass all pagination parameters to fetch_role_assignments."""
        info = MagicMock()
        mock_connection = MagicMock(spec=RoleAssignmentConnection)

        with (
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.current_user",
                return_value=user_data,
            ),
            patch(
                "ai.backend.manager.api.gql.rbac.resolver.role.fetch_role_assignments",
                new_callable=AsyncMock,
                return_value=mock_connection,
            ) as mock_fetch,
        ):
            resolver_fn = role_resolver.my_roles.base_resolver
            await resolver_fn(
                info,
                None,  # filter
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
