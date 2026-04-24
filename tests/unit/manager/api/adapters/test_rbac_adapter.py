"""Unit tests for RBACAdapter effective permissions methods."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.permission.types import OperationType
from ai.backend.common.dto.manager.v2.rbac.request import (
    ResolveEffectivePermissionsInput,
    ResolveUserEffectivePermissionsInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    EffectivePermissionsPayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import OperationTypeDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.services.permission_contoller.actions.resolve_effective_permissions import (
    ResolveEffectivePermissionsActionResult,
)


def _make_mock_processors() -> MagicMock:
    processors = MagicMock()
    processors.permission_controller.resolve_effective_permissions.wait_for_complete = AsyncMock()
    return processors


class TestResolveEffectivePermissions:
    @pytest.fixture
    def mock_processors(self) -> MagicMock:
        return _make_mock_processors()

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> RBACAdapter:
        return RBACAdapter(mock_processors)

    async def test_admin_resolve_returns_payload(
        self,
        adapter: RBACAdapter,
        mock_processors: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        permissions: Mapping[str, set[OperationType]] = {
            "entity-1": {OperationType.READ, OperationType.UPDATE},
            "entity-2": {OperationType.READ},
        }
        mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.return_value = ResolveEffectivePermissionsActionResult(
            permissions=permissions
        )

        input_dto = ResolveUserEffectivePermissionsInput(
            user_id=user_id,
            target_element_type="vfolder",
            target_entity_ids=["entity-1", "entity-2"],
        )
        result = await adapter.resolve_effective_permissions(input_dto)

        assert isinstance(result, EffectivePermissionsPayload)
        assert len(result.items) == 2
        entity_map = {item.entity_id: item.operations for item in result.items}
        assert OperationTypeDTO.READ in entity_map["entity-1"]
        assert OperationTypeDTO.UPDATE in entity_map["entity-1"]
        assert OperationTypeDTO.READ in entity_map["entity-2"]

    async def test_admin_resolve_passes_correct_action(
        self,
        adapter: RBACAdapter,
        mock_processors: MagicMock,
    ) -> None:
        user_id = uuid.uuid4()
        mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.return_value = ResolveEffectivePermissionsActionResult(
            permissions={}
        )

        input_dto = ResolveUserEffectivePermissionsInput(
            user_id=user_id,
            target_element_type="session",
            target_entity_ids=["s-1"],
            permission_entity_type="session",
        )
        await adapter.resolve_effective_permissions(input_dto)

        call_args = mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.user_id == user_id
        assert action.target_element_type.value == "session"
        assert action.target_entity_ids == ["s-1"]
        assert action.permission_entity_type is not None
        assert action.permission_entity_type.value == "session"

    async def test_admin_resolve_empty_entities(
        self,
        adapter: RBACAdapter,
        mock_processors: MagicMock,
    ) -> None:
        mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.return_value = ResolveEffectivePermissionsActionResult(
            permissions={}
        )

        input_dto = ResolveUserEffectivePermissionsInput(
            user_id=uuid.uuid4(),
            target_element_type="vfolder",
            target_entity_ids=[],
        )
        result = await adapter.resolve_effective_permissions(input_dto)

        assert result.items == []

    async def test_my_resolve_uses_current_user(
        self,
        adapter: RBACAdapter,
        mock_processors: MagicMock,
    ) -> None:
        my_user_id = uuid.uuid4()
        mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.return_value = ResolveEffectivePermissionsActionResult(
            permissions={"vf-1": {OperationType.READ}}
        )

        mock_user = MagicMock()
        mock_user.user_id = my_user_id

        input_dto = ResolveEffectivePermissionsInput(
            target_element_type="vfolder",
            target_entity_ids=["vf-1"],
        )
        with patch(
            "ai.backend.manager.api.adapters.rbac.adapter.current_user",
            return_value=mock_user,
        ):
            result = await adapter.my_resolve_effective_permissions(input_dto)

        call_args = mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.user_id == my_user_id
        assert isinstance(result, EffectivePermissionsPayload)
        assert len(result.items) == 1

    async def test_operations_are_sorted(
        self,
        adapter: RBACAdapter,
        mock_processors: MagicMock,
    ) -> None:
        permissions: Mapping[str, set[OperationType]] = {
            "e-1": {OperationType.UPDATE, OperationType.CREATE, OperationType.READ},
        }
        mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.return_value = ResolveEffectivePermissionsActionResult(
            permissions=permissions
        )

        input_dto = ResolveUserEffectivePermissionsInput(
            user_id=uuid.uuid4(),
            target_element_type="vfolder",
            target_entity_ids=["e-1"],
        )
        result = await adapter.resolve_effective_permissions(input_dto)

        ops = result.items[0].operations
        assert ops == sorted(ops, key=lambda o: o.value)

    async def test_entities_are_sorted_by_id(
        self,
        adapter: RBACAdapter,
        mock_processors: MagicMock,
    ) -> None:
        permissions: Mapping[str, set[OperationType]] = {
            "z-entity": {OperationType.READ},
            "a-entity": {OperationType.READ},
            "m-entity": {OperationType.READ},
        }
        mock_processors.permission_controller.resolve_effective_permissions.wait_for_complete.return_value = ResolveEffectivePermissionsActionResult(
            permissions=permissions
        )

        input_dto = ResolveUserEffectivePermissionsInput(
            user_id=uuid.uuid4(),
            target_element_type="vfolder",
            target_entity_ids=["z-entity", "a-entity", "m-entity"],
        )
        result = await adapter.resolve_effective_permissions(input_dto)

        entity_ids = [item.entity_id for item in result.items]
        assert entity_ids == ["a-entity", "m-entity", "z-entity"]
