"""purge_images (agent image force purge) passes the privilege check for a superadmin only."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from graphql import OperationType

from ai.backend.common.exception import PermissionDeniedError
from ai.backend.manager.api.gql_legacy.schema import GQLMutationPrivilegeCheckMiddleware
from ai.backend.manager.models.user.row import UserRole


class TestPurgeImagesSuperadminOnly:
    def _resolve_as(self, role: UserRole) -> MagicMock:
        """Run the privilege check for ``purge_images``; the returned mock is the resolver."""
        info = MagicMock()
        info.operation.operation = OperationType.MUTATION
        info.field_name = "purge_images"
        info.context.user = {"role": role}
        resolver = MagicMock()
        GQLMutationPrivilegeCheckMiddleware().resolve(resolver, None, info)
        return resolver

    def test_a_superadmin_reaches_the_resolver(self) -> None:
        self._resolve_as(UserRole.SUPERADMIN).assert_called_once()

    @pytest.mark.parametrize(
        "role",
        [UserRole.ADMIN, UserRole.USER, UserRole.MONITOR],
        ids=["admin", "user", "monitor"],
    )
    def test_any_other_role_is_denied(self, role: UserRole) -> None:
        with pytest.raises(PermissionDeniedError):
            self._resolve_as(role)
