"""The container registry quota mutations pass the privilege check for a superadmin only,
as the REST endpoints do."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from graphql import OperationType

from ai.backend.manager.api.gql_legacy.schema import GQLMutationPrivilegeCheckMiddleware
from ai.backend.manager.models.user.row import UserRole

QUOTA_MUTATIONS = [
    "create_container_registry_quota",
    "update_container_registry_quota",
    "delete_container_registry_quota",
]


class TestContainerRegistryQuotaSuperadminOnly:
    def _resolve_as(self, field_name: str, role: UserRole) -> MagicMock:
        """Run the privilege check for the mutation; the returned mock is the resolver."""
        info = MagicMock()
        info.operation.operation = OperationType.MUTATION
        info.field_name = field_name
        info.context.user = {"role": role}
        resolver = MagicMock()
        try:
            GQLMutationPrivilegeCheckMiddleware().resolve(resolver, None, info)
        except Exception:
            pass
        return resolver

    @pytest.mark.parametrize("field_name", QUOTA_MUTATIONS)
    def test_a_superadmin_reaches_the_resolver(self, field_name: str) -> None:
        self._resolve_as(field_name, UserRole.SUPERADMIN).assert_called_once()

    @pytest.mark.parametrize("field_name", QUOTA_MUTATIONS)
    @pytest.mark.parametrize(
        "role",
        [UserRole.ADMIN, UserRole.USER, UserRole.MONITOR],
        ids=["admin", "user", "monitor"],
    )
    def test_any_other_role_does_not_reach_the_resolver(
        self, field_name: str, role: UserRole
    ) -> None:
        self._resolve_as(field_name, role).assert_not_called()
