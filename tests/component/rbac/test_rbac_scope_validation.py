"""Component tests for scope_id validation in RBACAdapter."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.rbac import CreateRoleInput
from ai.backend.common.dto.manager.v2.rbac.request import (
    CreatePermissionInput,
    UpdatePermissionInput,
)
from ai.backend.common.dto.manager.v2.rbac.types import RBACElementTypeDTO, ScopeInputDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.models.rbac.exceptions import InvalidScope


@pytest.fixture()
def adapter() -> RBACAdapter:
    return RBACAdapter(MagicMock())


class TestValidateScopeId:
    """Adapter rejects non-UUID scope_id for USER / PROJECT scopes."""

    @pytest.mark.parametrize("scope_type", [RBACElementType.USER, RBACElementType.PROJECT])
    def test_rejects_email_as_scope_id(
        self,
        adapter: RBACAdapter,
        scope_type: RBACElementType,
    ) -> None:
        with pytest.raises(InvalidScope):
            adapter._validate_scope_id(scope_type, "alice@example.com")

    @pytest.mark.parametrize("scope_type", [RBACElementType.USER, RBACElementType.PROJECT])
    def test_accepts_valid_uuid_scope_id(
        self,
        adapter: RBACAdapter,
        scope_type: RBACElementType,
    ) -> None:
        adapter._validate_scope_id(scope_type, str(uuid.uuid4()))

    def test_accepts_string_scope_id_for_domain(
        self,
        adapter: RBACAdapter,
    ) -> None:
        adapter._validate_scope_id(RBACElementType.DOMAIN, "default")


class TestCreateRoleScopeValidation:
    """create() rejects invalid scope_id before calling processor."""

    async def test_rejects_email_in_user_scope(self, adapter: RBACAdapter) -> None:
        input_ = CreateRoleInput(
            name="bad-role",
            scopes=[
                ScopeInputDTO(scope_type=RBACElementTypeDTO.USER, scope_id="alice@example.com")
            ],
        )
        with pytest.raises(InvalidScope):
            await adapter.create(input_)

    async def test_rejects_email_in_project_scope(self, adapter: RBACAdapter) -> None:
        input_ = CreateRoleInput(
            name="bad-role",
            scopes=[
                ScopeInputDTO(scope_type=RBACElementTypeDTO.PROJECT, scope_id="not-a-uuid"),
            ],
        )
        with pytest.raises(InvalidScope):
            await adapter.create(input_)


class TestCreatePermissionScopeValidation:
    """create_permission() rejects invalid scope_id before calling processor."""

    async def test_rejects_email_in_user_scope(self, adapter: RBACAdapter) -> None:
        input_ = CreatePermissionInput(
            role_id=uuid.uuid4(),
            scope_type="user",
            scope_id="alice@example.com",
            entity_type="session",
            operation="read",
        )
        with pytest.raises(InvalidScope):
            await adapter.create_permission(input_)


class TestUpdatePermissionScopeValidation:
    """update_permission() rejects invalid scope_id before calling processor."""

    async def test_rejects_email_in_user_scope(self, adapter: RBACAdapter) -> None:
        input_ = UpdatePermissionInput(
            id=uuid.uuid4(),
            scope_type="user",
            scope_id="alice@example.com",
        )
        with pytest.raises(InvalidScope):
            await adapter.update_permission(input_)
