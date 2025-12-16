"""
Simple tests for Project Resource Policy Service functionality.
Tests the core project resource policy service actions to verify functionality.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.project_resource_policy.creators import (
    ProjectResourcePolicyCreatorSpec,
)
from ai.backend.manager.repositories.project_resource_policy.repository import (
    ProjectResourcePolicyRepository,
)
from ai.backend.manager.repositories.project_resource_policy.updaters import (
    ProjectResourcePolicyUpdaterSpec,
)
from ai.backend.manager.services.project_resource_policy.actions.create_project_resource_policy import (
    CreateProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.delete_project_resource_policy import (
    DeleteProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.actions.modify_project_resource_policy import (
    ModifyProjectResourcePolicyAction,
)
from ai.backend.manager.services.project_resource_policy.service import (
    ProjectResourcePolicyService,
)
from ai.backend.manager.types import OptionalState


class TestProjectResourcePolicyService:
    """Test project resource policy service functionality."""

    @pytest.fixture
    def mock_dependencies(self) -> dict[str, Any]:
        """Create mocked dependencies for testing."""
        project_resource_policy_repository = MagicMock(spec=ProjectResourcePolicyRepository)

        # Setup async methods
        project_resource_policy_repository.create = AsyncMock()
        project_resource_policy_repository.update = AsyncMock()
        project_resource_policy_repository.delete = AsyncMock()
        project_resource_policy_repository.get_by_name = AsyncMock()

        return {
            "project_resource_policy_repository": project_resource_policy_repository,
        }

    @pytest.fixture
    def project_resource_policy_service(self, mock_dependencies):
        """Create ProjectResourcePolicyService instance with mocked dependencies."""
        return ProjectResourcePolicyService(
            project_resource_policy_repository=mock_dependencies[
                "project_resource_policy_repository"
            ]
        )

    @pytest.mark.asyncio
    async def test_create_project_resource_policy(
        self, project_resource_policy_service, mock_dependencies
    ) -> None:
        """Test that CreateProjectResourcePolicyAction creates a policy correctly."""
        # Mock successful policy creation
        mock_policy_data = ProjectResourcePolicyRow(
            name="test-policy",
            max_vfolder_count=20,
            max_quota_scope_size=2147483648,  # 2GB
            max_network_count=5,
        )

        mock_dependencies["project_resource_policy_repository"].create = AsyncMock(
            return_value=mock_policy_data
        )

        action = CreateProjectResourcePolicyAction(
            creator=Creator(
                spec=ProjectResourcePolicyCreatorSpec(
                    name="test-policy",
                    max_vfolder_count=20,
                    max_quota_scope_size=2147483648,  # 2GB
                    max_network_count=5,
                )
            ),
        )

        result = await project_resource_policy_service.create_project_resource_policy(action)

        # Verify the repository was called correctly
        mock_dependencies["project_resource_policy_repository"].create.assert_called_once()
        call_args = mock_dependencies["project_resource_policy_repository"].create.call_args[0][0]
        assert isinstance(call_args, Creator)
        assert isinstance(call_args.spec, ProjectResourcePolicyCreatorSpec)
        assert call_args.spec.name == "test-policy"
        assert call_args.spec.max_vfolder_count == 20
        assert call_args.spec.max_quota_scope_size == 2147483648
        assert call_args.spec.max_network_count == 5

        # Verify the result
        assert result.project_resource_policy.name == "test-policy"
        assert result.project_resource_policy.max_vfolder_count == 20
        assert result.project_resource_policy.max_quota_scope_size == 2147483648
        assert result.project_resource_policy.max_network_count == 5

    @pytest.mark.asyncio
    async def test_modify_project_resource_policy(
        self, project_resource_policy_service, mock_dependencies
    ) -> None:
        """Test that ModifyProjectResourcePolicyAction modifies a policy correctly."""
        # Mock successful policy modification
        mock_modified_policy = ProjectResourcePolicyRow(
            name="modify-test-policy",
            max_vfolder_count=30,
            max_quota_scope_size=3221225472,  # 3GB
            max_network_count=10,
        )

        mock_dependencies["project_resource_policy_repository"].update = AsyncMock(
            return_value=mock_modified_policy
        )

        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(30),
            max_quota_scope_size=OptionalState.update(3221225472),  # 3GB
            max_network_count=OptionalState.update(10),
        )
        action = ModifyProjectResourcePolicyAction(
            name="modify-test-policy",
            updater=Updater(spec=spec, pk_value="modify-test-policy"),
        )

        result = await project_resource_policy_service.modify_project_resource_policy(action)

        # Verify the repository was called correctly with the Updater
        mock_dependencies["project_resource_policy_repository"].update.assert_called_once()
        call_args = mock_dependencies["project_resource_policy_repository"].update.call_args[0][0]
        assert isinstance(call_args, Updater)
        assert call_args.pk_value == "modify-test-policy"
        # Verify the spec values
        values = call_args.spec.build_values()
        assert values["max_vfolder_count"] == 30
        assert values["max_quota_scope_size"] == 3221225472
        assert values["max_network_count"] == 10

        # Verify the result
        assert result.project_resource_policy.name == "modify-test-policy"
        assert result.project_resource_policy.max_vfolder_count == 30
        assert result.project_resource_policy.max_quota_scope_size == 3221225472
        assert result.project_resource_policy.max_network_count == 10

    @pytest.mark.asyncio
    async def test_modify_project_resource_policy_not_found(
        self, project_resource_policy_service, mock_dependencies
    ) -> None:
        """Test that ModifyProjectResourcePolicyAction handles non-existent policy."""
        # Mock repository to raise ObjectNotFound
        mock_dependencies["project_resource_policy_repository"].update = AsyncMock(
            side_effect=ObjectNotFound(
                "Project resource policy with name non-existent-policy not found."
            )
        )

        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(30),
        )
        action = ModifyProjectResourcePolicyAction(
            name="non-existent-policy",
            updater=Updater(spec=spec, pk_value="non-existent-policy"),
        )

        with pytest.raises(ObjectNotFound) as exc_info:
            await project_resource_policy_service.modify_project_resource_policy(action)

        assert "Project resource policy with name non-existent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_delete_project_resource_policy(
        self, project_resource_policy_service, mock_dependencies
    ) -> None:
        """Test that DeleteProjectResourcePolicyAction deletes a policy correctly."""
        # Mock successful policy deletion
        mock_deleted_policy = ProjectResourcePolicyRow(
            name="delete-test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,  # 1GB
            max_network_count=1,
        )

        mock_dependencies["project_resource_policy_repository"].delete = AsyncMock(
            return_value=mock_deleted_policy
        )

        action = DeleteProjectResourcePolicyAction(name="delete-test-policy")

        result = await project_resource_policy_service.delete_project_resource_policy(action)

        # Verify the repository was called correctly
        mock_dependencies["project_resource_policy_repository"].delete.assert_called_once_with(
            "delete-test-policy"
        )

        # Verify the result
        assert result.project_resource_policy.name == "delete-test-policy"

    @pytest.mark.asyncio
    async def test_delete_project_resource_policy_not_found(
        self, project_resource_policy_service, mock_dependencies
    ) -> None:
        """Test that DeleteProjectResourcePolicyAction handles non-existent policy."""
        # Mock repository to raise ObjectNotFound
        mock_dependencies["project_resource_policy_repository"].delete = AsyncMock(
            side_effect=ObjectNotFound(
                "Project resource policy with name non-existent-policy not found."
            )
        )

        action = DeleteProjectResourcePolicyAction(name="non-existent-policy")

        with pytest.raises(ObjectNotFound) as exc_info:
            await project_resource_policy_service.delete_project_resource_policy(action)

        assert "Project resource policy with name non-existent-policy not found" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_partial_update_project_resource_policy(
        self, project_resource_policy_service, mock_dependencies
    ) -> None:
        """Test partial update of project resource policy."""
        # Mock successful partial update
        mock_modified_policy = ProjectResourcePolicyRow(
            name="partial-update-policy",
            max_vfolder_count=25,
            max_quota_scope_size=1073741824,  # 1GB (unchanged)
            max_network_count=1,  # Unchanged
        )

        mock_dependencies["project_resource_policy_repository"].update = AsyncMock(
            return_value=mock_modified_policy
        )

        # Update only max_vfolder_count, leave others unchanged
        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(25),
            # Other fields remain OptionalState.nop() by default
        )
        action = ModifyProjectResourcePolicyAction(
            name="partial-update-policy",
            updater=Updater(spec=spec, pk_value="partial-update-policy"),
        )

        result = await project_resource_policy_service.modify_project_resource_policy(action)

        # Verify the repository was called correctly with the Updater
        mock_dependencies["project_resource_policy_repository"].update.assert_called_once()
        call_args = mock_dependencies["project_resource_policy_repository"].update.call_args[0][0]
        assert isinstance(call_args, Updater)
        assert call_args.pk_value == "partial-update-policy"
        # Check that only max_vfolder_count was in the update fields
        values = call_args.spec.build_values()
        assert values["max_vfolder_count"] == 25
        assert "max_quota_scope_size" not in values  # Should not be included in partial update
        assert "max_network_count" not in values  # Should not be included in partial update

        # Verify the result
        assert result.project_resource_policy.name == "partial-update-policy"
        assert result.project_resource_policy.max_vfolder_count == 25
        assert result.project_resource_policy.max_quota_scope_size == 1073741824  # Unchanged
        assert result.project_resource_policy.max_network_count == 1  # Unchanged
