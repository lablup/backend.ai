"""Tests for permission mutation GraphQL resolvers."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.web_exceptions import HTTPForbidden

from ai.backend.common.dto.manager.v2.rbac.response import PermissionNode
from ai.backend.common.dto.manager.v2.rbac.types import OperationTypeDTO, RBACElementTypeDTO
from ai.backend.manager.api.gql.rbac.resolver import permission as permission_resolver
from ai.backend.manager.api.gql.rbac.types import PermissionGQL, UpdatePermissionInput
from ai.backend.manager.api.gql.rbac.types.permission import (
    OperationTypeGQL,
    RBACElementTypeGQL,
)


def _make_permission_node(
    *,
    permission_id: uuid.UUID | None = None,
    role_id: uuid.UUID | None = None,
    scope_type: RBACElementTypeDTO = RBACElementTypeDTO.DOMAIN,
    scope_id: str = "default",
    entity_type: RBACElementTypeDTO = RBACElementTypeDTO.VFOLDER,
    operation: OperationTypeDTO = OperationTypeDTO.READ,
) -> PermissionNode:
    return PermissionNode(
        id=permission_id or uuid.uuid4(),
        role_id=role_id or uuid.uuid4(),
        scope_type=scope_type,
        scope_id=scope_id,
        entity_type=entity_type,
        operation=operation,
    )


def _create_mock_info(update_permission_adapter: AsyncMock) -> MagicMock:
    info = MagicMock()
    info.context.adapters.rbac.update_permission = update_permission_adapter
    return info


class TestAdminUpdatePermission:
    @pytest.fixture(autouse=True)
    def _bypass_admin_check(self) -> Generator[None]:
        with patch("ai.backend.manager.api.gql.rbac.resolver.permission.check_admin_only"):
            yield

    @pytest.fixture
    def mock_adapter_method(self) -> AsyncMock:
        return AsyncMock()

    async def test_calls_processor_with_correct_action(
        self,
        mock_adapter_method: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        perm_node = _make_permission_node(
            permission_id=permission_id,
            operation=OperationTypeDTO.UPDATE,
        )
        mock_adapter_method.return_value = perm_node
        info = _create_mock_info(mock_adapter_method)

        input_data = UpdatePermissionInput(
            id=permission_id,
            operation=OperationTypeGQL.UPDATE,
        )

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        result = await resolver_fn(info=info, input=input_data)

        mock_adapter_method.assert_called_once()
        assert isinstance(result, PermissionGQL)

    async def test_partial_update_only_operation(
        self,
        mock_adapter_method: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        perm_node = _make_permission_node(
            permission_id=permission_id,
            operation=OperationTypeDTO.UPDATE,
        )
        mock_adapter_method.return_value = perm_node
        info = _create_mock_info(mock_adapter_method)

        input_data = UpdatePermissionInput(
            id=permission_id,
            operation=OperationTypeGQL.UPDATE,
        )
        dto = input_data.to_pydantic()

        assert dto.id == permission_id
        assert dto.operation is not None
        assert dto.scope_type is None
        assert dto.scope_id is None
        assert dto.entity_type is None

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        result = await resolver_fn(info=info, input=input_data)
        assert isinstance(result, PermissionGQL)

    async def test_full_update_all_fields(
        self,
        mock_adapter_method: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        perm_node = _make_permission_node(
            permission_id=permission_id,
            scope_type=RBACElementTypeDTO.PROJECT,
            scope_id="project-1",
            entity_type=RBACElementTypeDTO.SESSION,
            operation=OperationTypeDTO.CREATE,
        )
        mock_adapter_method.return_value = perm_node
        info = _create_mock_info(mock_adapter_method)

        input_data = UpdatePermissionInput(
            id=permission_id,
            scope_type=RBACElementTypeGQL.PROJECT,
            scope_id="project-1",
            entity_type=RBACElementTypeGQL.SESSION,
            operation=OperationTypeGQL.CREATE,
        )
        dto = input_data.to_pydantic()

        assert dto.id == permission_id
        assert dto.scope_type is not None
        assert dto.scope_id == "project-1"
        assert dto.entity_type is not None
        assert dto.operation is not None

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        result = await resolver_fn(info=info, input=input_data)
        assert isinstance(result, PermissionGQL)

    async def test_propagates_exception(
        self,
        mock_adapter_method: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        mock_adapter_method.side_effect = ValueError(
            f"Permission with ID {permission_id} does not exist."
        )
        info = _create_mock_info(mock_adapter_method)

        input_data = UpdatePermissionInput(
            id=permission_id,
            operation=OperationTypeGQL.READ,
        )

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        with pytest.raises(ValueError):
            await resolver_fn(info=info, input=input_data)

    async def test_returns_correct_gql_fields(
        self,
        mock_adapter_method: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        role_id = uuid.uuid4()
        perm_node = _make_permission_node(
            permission_id=permission_id,
            role_id=role_id,
            scope_type=RBACElementTypeDTO.DOMAIN,
            scope_id="default",
            entity_type=RBACElementTypeDTO.VFOLDER,
            operation=OperationTypeDTO.READ,
        )
        mock_adapter_method.return_value = perm_node
        info = _create_mock_info(mock_adapter_method)

        input_data = UpdatePermissionInput(
            id=permission_id,
            operation=OperationTypeGQL.READ,
        )

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        result = await resolver_fn(info=info, input=input_data)

        assert isinstance(result, PermissionGQL)
        assert result.role_id == role_id
        assert result.scope_type == RBACElementTypeGQL.DOMAIN
        assert result.scope_id == "default"
        assert result.entity_type == RBACElementTypeGQL.VFOLDER
        assert result.operation == OperationTypeGQL.READ


class TestAdminUpdatePermissionAccessControl:
    async def test_rejects_non_superadmin(self) -> None:
        info = MagicMock()
        input_data = UpdatePermissionInput(
            id=uuid.uuid4(),
            operation=OperationTypeGQL.READ,
        )

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        with pytest.raises(HTTPForbidden):
            await resolver_fn(info=info, input=input_data)
