"""Tests for permission mutation GraphQL resolvers."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.api.gql.rbac.resolver import permission as permission_resolver
from ai.backend.manager.api.gql.rbac.types import PermissionGQL, UpdatePermissionInput
from ai.backend.manager.api.gql.rbac.types.permission import (
    OperationTypeGQL,
    RBACElementTypeGQL,
)
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.services.permission_contoller.actions.update_permission import (
    UpdatePermissionAction,
    UpdatePermissionActionResult,
)


def _make_permission_data(
    *,
    permission_id: uuid.UUID | None = None,
    role_id: uuid.UUID | None = None,
    scope_type: ScopeType = ScopeType.DOMAIN,
    scope_id: str = "default",
    entity_type: EntityType = EntityType.VFOLDER,
    operation: OperationType = OperationType.READ,
) -> PermissionData:
    return PermissionData(
        id=permission_id or uuid.uuid4(),
        role_id=role_id or uuid.uuid4(),
        scope_type=scope_type,
        scope_id=scope_id,
        entity_type=entity_type,
        operation=operation,
    )


def _create_mock_context(update_permission_processor: AsyncMock) -> MagicMock:
    context = MagicMock()
    context.processors = MagicMock()
    context.processors.permission_controller = MagicMock()
    context.processors.permission_controller.update_permission = update_permission_processor
    return context


def _create_mock_info(context: MagicMock) -> MagicMock:
    info = MagicMock()
    info.context = context
    return info


class TestAdminUpdatePermission:
    @pytest.fixture(autouse=True)
    def _bypass_admin_check(self) -> None:
        with patch("ai.backend.manager.api.gql.rbac.resolver.permission.check_admin_only"):
            yield

    @pytest.fixture
    def mock_processor(self) -> AsyncMock:
        processor = AsyncMock()
        processor.wait_for_complete = AsyncMock()
        return processor

    async def test_calls_processor_with_correct_action(
        self,
        mock_processor: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        perm_data = _make_permission_data(
            permission_id=permission_id,
            operation=OperationType.UPDATE,
        )
        mock_processor.wait_for_complete.return_value = UpdatePermissionActionResult(
            data=perm_data,
        )
        context = _create_mock_context(mock_processor)
        info = _create_mock_info(context)

        input_data = UpdatePermissionInput(
            id=permission_id,
            operation=OperationTypeGQL.UPDATE,
        )

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        result = await resolver_fn(info=info, input=input_data)

        mock_processor.wait_for_complete.assert_called_once()
        call_args = mock_processor.wait_for_complete.call_args
        action = call_args[0][0]
        assert isinstance(action, UpdatePermissionAction)
        assert action.updater.pk_value == permission_id

        assert isinstance(result, PermissionGQL)

    async def test_partial_update_only_operation(
        self,
        mock_processor: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        perm_data = _make_permission_data(
            permission_id=permission_id,
            operation=OperationType.UPDATE,
        )
        mock_processor.wait_for_complete.return_value = UpdatePermissionActionResult(
            data=perm_data,
        )
        context = _create_mock_context(mock_processor)
        info = _create_mock_info(context)

        input_data = UpdatePermissionInput(
            id=permission_id,
            operation=OperationTypeGQL.UPDATE,
        )
        updater = input_data.to_updater()
        values = updater.spec.build_values()

        assert "operation" in values
        assert values["operation"] == OperationType.UPDATE
        assert "scope_type" not in values
        assert "scope_id" not in values
        assert "entity_type" not in values

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        result = await resolver_fn(info=info, input=input_data)
        assert isinstance(result, PermissionGQL)

    async def test_full_update_all_fields(
        self,
        mock_processor: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        perm_data = _make_permission_data(
            permission_id=permission_id,
            scope_type=ScopeType.PROJECT,
            scope_id="project-1",
            entity_type=EntityType.SESSION,
            operation=OperationType.CREATE,
        )
        mock_processor.wait_for_complete.return_value = UpdatePermissionActionResult(
            data=perm_data,
        )
        context = _create_mock_context(mock_processor)
        info = _create_mock_info(context)

        input_data = UpdatePermissionInput(
            id=permission_id,
            scope_type=RBACElementTypeGQL.PROJECT,
            scope_id="project-1",
            entity_type=RBACElementTypeGQL.SESSION,
            operation=OperationTypeGQL.CREATE,
        )
        updater = input_data.to_updater()
        values = updater.spec.build_values()

        assert values["scope_type"] == ScopeType.PROJECT
        assert values["scope_id"] == "project-1"
        assert values["entity_type"] == EntityType.SESSION
        assert values["operation"] == OperationType.CREATE

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        result = await resolver_fn(info=info, input=input_data)
        assert isinstance(result, PermissionGQL)

    async def test_propagates_object_not_found(
        self,
        mock_processor: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        mock_processor.wait_for_complete.side_effect = ObjectNotFound(
            f"Permission with ID {permission_id} does not exist."
        )
        context = _create_mock_context(mock_processor)
        info = _create_mock_info(context)

        input_data = UpdatePermissionInput(
            id=permission_id,
            operation=OperationTypeGQL.READ,
        )

        resolver_fn = permission_resolver.admin_update_permission.base_resolver
        with pytest.raises(ObjectNotFound):
            await resolver_fn(info=info, input=input_data)

    async def test_returns_correct_gql_fields(
        self,
        mock_processor: AsyncMock,
    ) -> None:
        permission_id = uuid.uuid4()
        role_id = uuid.uuid4()
        perm_data = _make_permission_data(
            permission_id=permission_id,
            role_id=role_id,
            scope_type=ScopeType.DOMAIN,
            scope_id="default",
            entity_type=EntityType.VFOLDER,
            operation=OperationType.READ,
        )
        mock_processor.wait_for_complete.return_value = UpdatePermissionActionResult(
            data=perm_data,
        )
        context = _create_mock_context(mock_processor)
        info = _create_mock_info(context)

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
