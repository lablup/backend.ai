"""
Unit tests for PermissionControllerService.resolve_effective_permissions.
Tests the service layer using a mocked repository.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RBACElementType,
)
from ai.backend.manager.data.permission.role import (
    EffectivePermissionsInput,
    EffectivePermissionsResult,
)
from ai.backend.manager.services.permission_contoller.actions.resolve_effective_permissions import (
    ResolveEffectivePermissionsAction,
)
from ai.backend.manager.services.permission_contoller.service import (
    PermissionControllerService,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.permission_controller.repository import (
        PermissionControllerRepository,
    )


class TestResolveEffectivePermissions:
    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        repository = MagicMock()
        repository.resolve_effective_permissions = AsyncMock()
        return repository

    @pytest.fixture
    def service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        return PermissionControllerService(
            repository=mock_repository,
            group_repository=MagicMock(),
            rbac_action_registry=[],
        )

    async def test_delegates_to_repository_with_correct_input(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        entity_ids = ["entity-1", "entity-2"]
        mock_repository.resolve_effective_permissions.return_value = EffectivePermissionsResult(
            permissions={
                "entity-1": {OperationType.READ},
                "entity-2": {OperationType.READ, OperationType.UPDATE},
            }
        )

        action = ResolveEffectivePermissionsAction(
            user_id=user_id,
            target_element_type=RBACElementType.VFOLDER,
            target_entity_ids=entity_ids,
        )
        result = await service.resolve_effective_permissions(action)

        mock_repository.resolve_effective_permissions.assert_called_once()
        call_arg = mock_repository.resolve_effective_permissions.call_args[0][0]
        assert isinstance(call_arg, EffectivePermissionsInput)
        assert call_arg.user_id == user_id
        assert call_arg.target_element_type == RBACElementType.VFOLDER
        assert call_arg.target_entity_ids == entity_ids
        assert call_arg.permission_entity_type is None

        assert result.permissions["entity-1"] == {OperationType.READ}
        assert result.permissions["entity-2"] == {OperationType.READ, OperationType.UPDATE}

    async def test_forwards_permission_entity_type(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        mock_repository.resolve_effective_permissions.return_value = EffectivePermissionsResult(
            permissions={}
        )

        action = ResolveEffectivePermissionsAction(
            user_id=user_id,
            target_element_type=RBACElementType.SESSION,
            target_entity_ids=["s-1"],
            permission_entity_type=EntityType.SESSION,
        )
        await service.resolve_effective_permissions(action)

        call_arg = mock_repository.resolve_effective_permissions.call_args[0][0]
        assert call_arg.permission_entity_type == EntityType.SESSION

    async def test_empty_entity_ids(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.resolve_effective_permissions.return_value = EffectivePermissionsResult(
            permissions={}
        )

        action = ResolveEffectivePermissionsAction(
            user_id=uuid.uuid4(),
            target_element_type=RBACElementType.VFOLDER,
            target_entity_ids=[],
        )
        result = await service.resolve_effective_permissions(action)

        mock_repository.resolve_effective_permissions.assert_called_once()
        assert result.permissions == {}

    async def test_returns_empty_operations_for_no_permissions(
        self,
        service: PermissionControllerService,
        mock_repository: MagicMock,
    ) -> None:
        mock_repository.resolve_effective_permissions.return_value = EffectivePermissionsResult(
            permissions={"entity-1": set()}
        )

        action = ResolveEffectivePermissionsAction(
            user_id=uuid.uuid4(),
            target_element_type=RBACElementType.VFOLDER,
            target_entity_ids=["entity-1"],
        )
        result = await service.resolve_effective_permissions(action)

        assert result.permissions["entity-1"] == set()
