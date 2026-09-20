"""
Tests for RBAC API handlers (scope-related endpoints).
Tests the get_scope_types handler by directly calling the
new constructor-DI based RBACHandler methods with typed parameters.
"""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.permission_contoller.actions.get_scope_types import (
    PublicGetScopeTypesActionResult,
)


def make_test_handler(mock_permission_controller: MagicMock) -> RBACHandler:
    """Create an RBACHandler with mock permission controller processors."""
    return RBACHandler(permission_controller=mock_permission_controller, rbac=MagicMock())


def make_test_superadmin_ctx() -> UserContext:
    """Create a UserContext for a superadmin user."""
    return UserContext(
        user_uuid=uuid4(),
        user_email="admin@test.com",
        user_domain="default",
        user_role=UserRole.SUPERADMIN,
        access_key="TESTKEY",
        is_admin=True,
        is_superadmin=True,
    )


class TestGetScopeTypesHandler:
    """Tests for get_scope_types handler."""

    SCOPE_TYPES: list[EntityType] = [DomainEntityType(), ProjectEntityType(), UserEntityType()]

    @pytest.fixture
    def mock_permission_controller(self) -> MagicMock:
        """Create mock permission controller processors."""
        pc = MagicMock()
        pc.public_get_scope_types = MagicMock()
        pc.public_get_scope_types.run = AsyncMock()
        return pc

    async def test_get_scope_types_returns_scope_types(
        self,
        mock_permission_controller: MagicMock,
    ) -> None:
        """Test get_scope_types returns all scope types."""
        handler = make_test_handler(mock_permission_controller)
        ctx = make_test_superadmin_ctx()
        action_result = PublicGetScopeTypesActionResult(entity_types=self.SCOPE_TYPES)
        mock_permission_controller.public_get_scope_types.run.return_value = action_result

        response = await handler.get_scope_types(ctx=ctx)

        assert response.status_code == HTTPStatus.OK
        response_json = response.to_json
        assert isinstance(response_json, dict)
        assert "items" in response_json
        assert response_json["items"] == self.SCOPE_TYPES
