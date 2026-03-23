"""
Unit tests for BaseRBACAction registry in PermissionControllerService.

Tests:
1. Registration completeness - verifies all concrete BaseRBACAction subclasses are registered
2. get_entity_valid_operations() method - verifies correct aggregation logic
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import BaseRBACAction
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
            rbac_action_registry=[],
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

        # Get registered classes from the service's registry
        registered_classes = set(empty_registry_service._rbac_action_registry)

        # Verify all concrete classes are registered
        for rbac_class in concrete_classes:
            assert rbac_class in registered_classes, (
                f"{rbac_class.__name__} is not registered in rbac_action_registry"
            )

        # Ensure no extra registrations
        expected_count = len(concrete_classes)
        actual_count = len(registered_classes)
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

    def test_get_entity_valid_operations_aggregation(
        self, mock_repository: PermissionControllerRepository
    ) -> None:
        """get_entity_valid_operations() correctly aggregates permissions by element type."""

        # Create mock RBAC action classes
        class MockUserReadAction(BaseRBACAction):
            @classmethod
            def required_permission(cls) -> tuple[RBACElementType, OperationType]:
                return (RBACElementType.USER, OperationType.READ)

        class MockUserCreateAction(BaseRBACAction):
            @classmethod
            def required_permission(cls) -> tuple[RBACElementType, OperationType]:
                return (RBACElementType.USER, OperationType.CREATE)

        class MockVFolderReadAction(BaseRBACAction):
            @classmethod
            def required_permission(cls) -> tuple[RBACElementType, OperationType]:
                return (RBACElementType.VFOLDER, OperationType.READ)

        class MockVFolderDeleteAction(BaseRBACAction):
            @classmethod
            def required_permission(cls) -> tuple[RBACElementType, OperationType]:
                return (RBACElementType.VFOLDER, OperationType.SOFT_DELETE)

        # Create service with populated registry (flat list)
        registry = [
            MockUserReadAction,
            MockUserCreateAction,
            MockVFolderReadAction,
            MockVFolderDeleteAction,
        ]
        service = PermissionControllerService(
            repository=mock_repository,
            rbac_action_registry=registry,
        )

        # Call get_entity_valid_operations
        result = service.get_entity_valid_operations()

        # Verify structure
        assert isinstance(result, dict)
        assert len(result) == 2
        assert RBACElementType.USER in result
        assert RBACElementType.VFOLDER in result

        # Verify USER operations (aggregated from 2 actions)
        user_ops = result[RBACElementType.USER]
        assert isinstance(user_ops, set)
        assert len(user_ops) == 2
        assert OperationType.READ in user_ops
        assert OperationType.CREATE in user_ops

        # Verify VFOLDER operations (aggregated from 2 actions)
        vfolder_ops = result[RBACElementType.VFOLDER]
        assert isinstance(vfolder_ops, set)
        assert len(vfolder_ops) == 2
        assert OperationType.READ in vfolder_ops
        assert OperationType.SOFT_DELETE in vfolder_ops

    def test_get_entity_valid_operations_deduplication(
        self, mock_repository: PermissionControllerRepository
    ) -> None:
        """get_entity_valid_operations() deduplicates operations for the same element type."""

        # Create multiple actions with the same permission
        class MockUserReadAction1(BaseRBACAction):
            @classmethod
            def required_permission(cls) -> tuple[RBACElementType, OperationType]:
                return (RBACElementType.USER, OperationType.READ)

        class MockUserReadAction2(BaseRBACAction):
            @classmethod
            def required_permission(cls) -> tuple[RBACElementType, OperationType]:
                return (RBACElementType.USER, OperationType.READ)

        registry = [MockUserReadAction1, MockUserReadAction2]
        service = PermissionControllerService(
            repository=mock_repository,
            rbac_action_registry=registry,
        )

        result = service.get_entity_valid_operations()

        # Should have only 1 operation despite 2 actions declaring the same permission
        assert RBACElementType.USER in result
        user_ops = result[RBACElementType.USER]
        assert len(user_ops) == 1
        assert OperationType.READ in user_ops
