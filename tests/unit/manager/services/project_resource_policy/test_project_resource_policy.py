"""
Simple tests for Project Resource Policy Service functionality.
Tests the core project resource policy service actions to verify functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.errors.common import ObjectNotFound
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

# ==================== Shared Fixtures ====================


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create mocked project resource policy repository."""
    return MagicMock(spec=ProjectResourcePolicyRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> ProjectResourcePolicyService:
    """Create ProjectResourcePolicyService with mocked dependencies."""
    return ProjectResourcePolicyService(
        project_resource_policy_repository=mock_repository,
    )


@pytest.fixture
def sample_policy_data() -> ProjectResourcePolicyData:
    """Create sample project resource policy data."""
    return ProjectResourcePolicyData(
        name="test-policy",
        max_vfolder_count=20,
        max_quota_scope_size=2147483648,  # 2GB
        max_network_count=5,
    )


# ==================== Create Tests ====================


class TestCreateProjectResourcePolicy:
    """Test cases for ProjectResourcePolicyService.create_project_resource_policy"""

    async def test_success(
        self,
        service: ProjectResourcePolicyService,
        mock_repository: MagicMock,
        sample_policy_data: ProjectResourcePolicyData,
    ) -> None:
        """Test that CreateProjectResourcePolicyAction creates a policy correctly."""
        mock_repository.create = AsyncMock(return_value=sample_policy_data)

        action = CreateProjectResourcePolicyAction(
            creator=Creator(
                spec=ProjectResourcePolicyCreatorSpec(
                    name="test-policy",
                    max_vfolder_count=20,
                    max_quota_scope_size=2147483648,
                    max_network_count=5,
                )
            ),
        )

        result = await service.create_project_resource_policy(action)

        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args[0][0]
        assert isinstance(call_args, Creator)
        assert isinstance(call_args.spec, ProjectResourcePolicyCreatorSpec)
        assert call_args.spec.name == "test-policy"
        assert call_args.spec.max_vfolder_count == 20
        assert call_args.spec.max_quota_scope_size == 2147483648
        assert call_args.spec.max_network_count == 5

        assert result.project_resource_policy.name == "test-policy"
        assert result.project_resource_policy.max_vfolder_count == 20
        assert result.project_resource_policy.max_quota_scope_size == 2147483648
        assert result.project_resource_policy.max_network_count == 5


# ==================== Modify Tests ====================


class TestModifyProjectResourcePolicy:
    """Test cases for ProjectResourcePolicyService.modify_project_resource_policy"""

    async def test_success(
        self,
        service: ProjectResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that ModifyProjectResourcePolicyAction modifies a policy correctly."""
        modified_policy_data = ProjectResourcePolicyData(
            name="modify-test-policy",
            max_vfolder_count=30,
            max_quota_scope_size=3221225472,  # 3GB
            max_network_count=10,
        )
        mock_repository.update = AsyncMock(return_value=modified_policy_data)

        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(30),
            max_quota_scope_size=OptionalState.update(3221225472),
            max_network_count=OptionalState.update(10),
        )
        action = ModifyProjectResourcePolicyAction(
            name="modify-test-policy",
            updater=Updater(spec=spec, pk_value="modify-test-policy"),
        )

        result = await service.modify_project_resource_policy(action)

        mock_repository.update.assert_called_once()
        call_args = mock_repository.update.call_args[0][0]
        assert isinstance(call_args, Updater)
        assert call_args.pk_value == "modify-test-policy"
        values = call_args.spec.build_values()
        assert values["max_vfolder_count"] == 30
        assert values["max_quota_scope_size"] == 3221225472
        assert values["max_network_count"] == 10

        assert result.project_resource_policy.name == "modify-test-policy"
        assert result.project_resource_policy.max_vfolder_count == 30
        assert result.project_resource_policy.max_quota_scope_size == 3221225472
        assert result.project_resource_policy.max_network_count == 10

    async def test_not_found(
        self,
        service: ProjectResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that ModifyProjectResourcePolicyAction handles non-existent policy."""
        mock_repository.update = AsyncMock(
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
            await service.modify_project_resource_policy(action)

        assert "Project resource policy with name non-existent-policy not found" in str(
            exc_info.value
        )

    async def test_partial_update(
        self,
        service: ProjectResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test partial update of project resource policy."""
        partial_update_data = ProjectResourcePolicyData(
            name="partial-update-policy",
            max_vfolder_count=25,
            max_quota_scope_size=1073741824,  # 1GB (unchanged)
            max_network_count=1,  # Unchanged
        )
        mock_repository.update = AsyncMock(return_value=partial_update_data)

        # Update only max_vfolder_count, leave others unchanged
        spec = ProjectResourcePolicyUpdaterSpec(
            max_vfolder_count=OptionalState.update(25),
        )
        action = ModifyProjectResourcePolicyAction(
            name="partial-update-policy",
            updater=Updater(spec=spec, pk_value="partial-update-policy"),
        )

        result = await service.modify_project_resource_policy(action)

        mock_repository.update.assert_called_once()
        call_args = mock_repository.update.call_args[0][0]
        assert isinstance(call_args, Updater)
        assert call_args.pk_value == "partial-update-policy"
        values = call_args.spec.build_values()
        assert values["max_vfolder_count"] == 25
        assert "max_quota_scope_size" not in values
        assert "max_network_count" not in values

        assert result.project_resource_policy.name == "partial-update-policy"
        assert result.project_resource_policy.max_vfolder_count == 25
        assert result.project_resource_policy.max_quota_scope_size == 1073741824
        assert result.project_resource_policy.max_network_count == 1


# ==================== Delete Tests ====================


class TestDeleteProjectResourcePolicy:
    """Test cases for ProjectResourcePolicyService.delete_project_resource_policy"""

    async def test_success(
        self,
        service: ProjectResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that DeleteProjectResourcePolicyAction deletes a policy correctly."""
        deleted_policy_data = ProjectResourcePolicyData(
            name="delete-test-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,  # 1GB
            max_network_count=1,
        )
        mock_repository.delete = AsyncMock(return_value=deleted_policy_data)

        action = DeleteProjectResourcePolicyAction(name="delete-test-policy")

        result = await service.delete_project_resource_policy(action)

        mock_repository.delete.assert_called_once_with("delete-test-policy")
        assert result.project_resource_policy.name == "delete-test-policy"

    async def test_not_found(
        self,
        service: ProjectResourcePolicyService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that DeleteProjectResourcePolicyAction handles non-existent policy."""
        mock_repository.delete = AsyncMock(
            side_effect=ObjectNotFound(
                "Project resource policy with name non-existent-policy not found."
            )
        )

        action = DeleteProjectResourcePolicyAction(name="non-existent-policy")

        with pytest.raises(ObjectNotFound) as exc_info:
            await service.delete_project_resource_policy(action)

        assert "Project resource policy with name non-existent-policy not found" in str(
            exc_info.value
        )
