"""The container registry quota mutations pass the privilege check for a superadmin only,
as the REST endpoints do."""

from __future__ import annotations

from typing import Any
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
    def _resolve_as(self, field_name: str, role: UserRole) -> tuple[MagicMock, Any]:
        """Run the privilege check for the mutation; answers the resolver mock and the result."""
        info = MagicMock()
        info.operation.operation = OperationType.MUTATION
        info.field_name = field_name
        info.path.key = field_name
        info.context.user = {"role": role}
        resolver = MagicMock()
        result = GQLMutationPrivilegeCheckMiddleware().resolve(resolver, None, info)
        return resolver, result

    @pytest.mark.parametrize("field_name", QUOTA_MUTATIONS)
    def test_a_superadmin_reaches_the_resolver(self, field_name: str) -> None:
        resolver, result = self._resolve_as(field_name, UserRole.SUPERADMIN)
        resolver.assert_called_once()
        assert result is resolver.return_value

    @pytest.mark.parametrize("field_name", QUOTA_MUTATIONS)
    @pytest.mark.parametrize(
        "role",
        [UserRole.ADMIN, UserRole.USER, UserRole.MONITOR],
        ids=["admin", "user", "monitor"],
    )
    def test_any_other_role_is_refused_before_the_resolver(
        self, field_name: str, role: UserRole
    ) -> None:
        resolver, result = self._resolve_as(field_name, role)
        resolver.assert_not_called()
        assert result.ok is False
        assert result.msg == f"no permission to execute {field_name}"
