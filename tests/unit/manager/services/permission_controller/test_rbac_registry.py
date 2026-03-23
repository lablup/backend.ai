"""
Unit tests for BaseRBACAction registry in PermissionControllerService.

Tests:
1. Registration completeness - verifies all concrete BaseRBACAction subclasses are registered
2. get_entity_valid_operations() method - verifies correct structure and behavior
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action.rbac import BaseRBACAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.permission_contoller.service import (
    PermissionControllerService,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.permission_controller.repository import (
        PermissionControllerRepository,
    )


def _collect_all_rbac_subclasses(cls: type[BaseRBACAction]) -> set[type[BaseRBACAction]]:
    """
    Recursively collect all concrete subclasses of BaseRBACAction.

    Args:
        cls: The base class to start from (BaseRBACAction)

    Returns:
        Set of all concrete (non-abstract) subclasses
    """
    all_subclasses = set()
    for subclass in cls.__subclasses__():
        # Recursively collect from subclasses
        all_subclasses.update(_collect_all_rbac_subclasses(subclass))
        # Add concrete classes only (not abstract)
        if not getattr(subclass, "__abstractmethods__", None):
            all_subclasses.add(subclass)
    return all_subclasses


class TestRBACRegistry:
    """Test BaseRBACAction registry functionality."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create a mock repository for testing."""
        return MagicMock()

    @pytest.fixture
    def empty_registry_service(
        self, mock_repository: PermissionControllerRepository
    ) -> PermissionControllerService:
        """Service with empty RBAC registry (initial state)."""
        return PermissionControllerService(
            repository=mock_repository,
            rbac_action_registry={},
        )

    def test_registration_completeness(
        self, empty_registry_service: PermissionControllerService
    ) -> None:
        """
        Verify all concrete BaseRBACAction subclasses are registered.

        This test will PASS initially (when registry is empty) because no concrete
        implementations exist yet. It will START FAILING when BA-5317~BA-5348
        add concrete implementations, which will force developers to register them.
        """
        # Collect all concrete BaseRBACAction subclasses
        concrete_classes = _collect_all_rbac_subclasses(BaseRBACAction)  # type: ignore[type-abstract]

        # Get registered entity types from the service's registry
        registered_entity_types = set(empty_registry_service._rbac_action_registry.keys())

        # For each concrete class, verify it's registered
        for rbac_class in concrete_classes:
            entity_type = rbac_class.entity_type()
            assert entity_type in registered_entity_types, (
                f"{rbac_class.__name__} (EntityType.{entity_type.name}) is not registered in rbac_action_registry"
            )

        # Ensure no extra registrations
        expected_count = len(concrete_classes)
        actual_count = len(registered_entity_types)
        assert actual_count == expected_count, (
            f"Registry has {actual_count} entries but {expected_count} concrete classes exist"
        )

    def test_get_entity_valid_operations_empty_registry(
        self, empty_registry_service: PermissionControllerService
    ) -> None:
        """get_entity_valid_operations() returns empty dict when registry is empty."""
        result = empty_registry_service.get_entity_valid_operations()

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_entity_valid_operations_with_mock_classes(
        self, mock_repository: PermissionControllerRepository
    ) -> None:
        """get_entity_valid_operations() returns correct structure with mock classes."""

        # Create mock RBAC action classes
        class MockUserRBACAction(BaseRBACAction):
            @classmethod
            def entity_type(cls) -> EntityType:
                return EntityType.USER

            @classmethod
            def valid_operations(cls) -> Mapping[ActionOperationType, str]:
                return {
                    ActionOperationType.GET: "Get user details",
                    ActionOperationType.SEARCH: "Search users",
                    ActionOperationType.CREATE: "Create new user",
                }

        class MockVFolderRBACAction(BaseRBACAction):
            @classmethod
            def entity_type(cls) -> EntityType:
                return EntityType.VFOLDER

            @classmethod
            def valid_operations(cls) -> Mapping[ActionOperationType, str]:
                return {
                    ActionOperationType.GET: "Get vfolder details",
                    ActionOperationType.DELETE: "Delete vfolder",
                }

        # Create service with populated registry
        registry = {
            EntityType.USER: MockUserRBACAction,
            EntityType.VFOLDER: MockVFolderRBACAction,
        }
        service = PermissionControllerService(
            repository=mock_repository,
            rbac_action_registry=registry,
        )

        # Call get_entity_valid_operations
        result = service.get_entity_valid_operations()

        # Verify structure
        assert isinstance(result, dict)
        assert len(result) == 2
        assert EntityType.USER in result
        assert EntityType.VFOLDER in result

        # Verify USER operations
        user_ops = result[EntityType.USER]
        assert isinstance(user_ops, Mapping)
        assert len(user_ops) == 3
        assert user_ops[ActionOperationType.GET] == "Get user details"
        assert user_ops[ActionOperationType.SEARCH] == "Search users"
        assert user_ops[ActionOperationType.CREATE] == "Create new user"

        # Verify VFOLDER operations
        vfolder_ops = result[EntityType.VFOLDER]
        assert isinstance(vfolder_ops, Mapping)
        assert len(vfolder_ops) == 2
        assert vfolder_ops[ActionOperationType.GET] == "Get vfolder details"
        assert vfolder_ops[ActionOperationType.DELETE] == "Delete vfolder"

    def test_get_entity_valid_operations_returns_new_dict(
        self, mock_repository: PermissionControllerRepository
    ) -> None:
        """get_entity_valid_operations() returns a new dict each time (immutability check)."""

        class MockUserRBACAction(BaseRBACAction):
            @classmethod
            def entity_type(cls) -> EntityType:
                return EntityType.USER

            @classmethod
            def valid_operations(cls) -> Mapping[ActionOperationType, str]:
                return {ActionOperationType.GET: "Get user"}

        registry = {EntityType.USER: MockUserRBACAction}
        service = PermissionControllerService(
            repository=mock_repository,
            rbac_action_registry=registry,
        )

        # Call twice
        result1 = service.get_entity_valid_operations()
        result2 = service.get_entity_valid_operations()

        # They should be equal in content but not the same object
        assert result1 == result2
        assert result1 is not result2  # Different dict instances
