"""Test for vfolder RBAC migration module."""

import uuid
from dataclasses import dataclass

import pytest

from ai.backend.manager.models.rbac_models.migrate.types import PermissionCreateInputGroup
from ai.backend.manager.models.rbac_models.migrate.vfolder import (
    ENTITY_TYPE,
    vfolder_permission_row_to_rbac_row,
    vfolder_row_to_rbac_row,
)
from ai.backend.manager.models.vfolder import VFolderOwnershipType


@dataclass
class MockVFolderRow:
    """Mock VFolderRow for testing."""

    id: uuid.UUID
    ownership_type: VFolderOwnershipType
    user: uuid.UUID | None = None
    group: uuid.UUID | None = None


@dataclass
class MockVFolderPermissionRow:
    """Mock VFolderPermissionRow for testing."""

    vfolder: uuid.UUID
    user: uuid.UUID


@pytest.fixture
def mock_user_vfolder():
    """Create a mock user-owned vfolder."""
    user_id = uuid.uuid4()
    vfolder_id = uuid.uuid4()
    return MockVFolderRow(
        id=vfolder_id,
        ownership_type=VFolderOwnershipType.USER,
        user=user_id,
        group=None,
    )


@pytest.fixture
def mock_project_vfolder():
    """Create a mock project-owned vfolder."""
    project_id = uuid.uuid4()
    vfolder_id = uuid.uuid4()
    return MockVFolderRow(
        id=vfolder_id,
        ownership_type=VFolderOwnershipType.GROUP,
        user=None,
        group=project_id,
    )


@pytest.fixture
def mock_vfolder_permission():
    """Create a mock vfolder permission."""
    return MockVFolderPermissionRow(
        vfolder=uuid.uuid4(),
        user=uuid.uuid4(),
    )


class TestVFolderConversion:
    """Test vfolder conversion functions."""

    def test_user_vfolder_to_rbac_row(self, mock_user_vfolder):
        """Test converting user-owned vfolder to RBAC row."""
        result = vfolder_row_to_rbac_row(mock_user_vfolder)

        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]

        assert assoc.scope_id.scope_type == "user"
        assert assoc.scope_id.scope_id == str(mock_user_vfolder.user)
        assert assoc.object_id.entity_type == ENTITY_TYPE
        assert assoc.object_id.entity_id == str(mock_user_vfolder.id)

    def test_project_vfolder_to_rbac_row(self, mock_project_vfolder):
        """Test converting project-owned vfolder to RBAC row."""
        result = vfolder_row_to_rbac_row(mock_project_vfolder)

        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]

        assert assoc.scope_id.scope_type == "project"
        assert assoc.scope_id.scope_id == str(mock_project_vfolder.group)
        assert assoc.object_id.entity_type == ENTITY_TYPE
        assert assoc.object_id.entity_id == str(mock_project_vfolder.id)

    def test_vfolder_permission_to_rbac_row(self, mock_vfolder_permission):
        """Test converting vfolder permission to RBAC row."""
        result = vfolder_permission_row_to_rbac_row(mock_vfolder_permission)

        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]

        assert assoc.scope_id.scope_type == "user"
        assert assoc.scope_id.scope_id == str(mock_vfolder_permission.user)
        assert assoc.object_id.entity_type == ENTITY_TYPE
        assert assoc.object_id.entity_id == str(mock_vfolder_permission.vfolder)


class TestComplexScenarios:
    """Test complex migration scenarios."""

    @pytest.fixture
    def test_data(self):
        """Create comprehensive test data."""
        users = {
            "owner": uuid.uuid4(),
            "member1": uuid.uuid4(),
            "member2": uuid.uuid4(),
        }

        projects = {
            "project1": uuid.uuid4(),
            "project2": uuid.uuid4(),
        }

        vfolders = {
            "user_vfolder": MockVFolderRow(
                id=uuid.uuid4(),
                ownership_type=VFolderOwnershipType.USER,
                user=users["owner"],
            ),
            "project_vfolder": MockVFolderRow(
                id=uuid.uuid4(),
                ownership_type=VFolderOwnershipType.GROUP,
                group=projects["project1"],
            ),
        }

        permissions = [
            MockVFolderPermissionRow(
                vfolder=vfolders["user_vfolder"].id,
                user=users["member1"],
            ),
            MockVFolderPermissionRow(
                vfolder=vfolders["user_vfolder"].id,
                user=users["member2"],
            ),
            MockVFolderPermissionRow(
                vfolder=vfolders["project_vfolder"].id,
                user=users["member1"],
            ),
        ]

        return {
            "users": users,
            "projects": projects,
            "vfolders": vfolders,
            "permissions": permissions,
        }

    def test_multiple_permissions_same_vfolder(self, test_data):
        """Test handling multiple permissions for the same vfolder."""
        vfolder: MockVFolderRow = test_data["vfolders"]["user_vfolder"]
        permissions: list[MockVFolderPermissionRow] = [
            p for p in test_data["permissions"] if p.vfolder == vfolder.id
        ]

        # Convert vfolder
        vfolder_result = vfolder_row_to_rbac_row(vfolder)
        assert len(vfolder_result.association_scopes_entities) == 1

        # Convert permissions
        permission_results: list[PermissionCreateInputGroup] = []
        for perm in permissions:
            result = vfolder_permission_row_to_rbac_row(perm)
            permission_results.append(result)

        # Verify each permission creates separate association
        assert len(permission_results) == 2
        for permission, permission_result in zip(permissions, permission_results):
            assert len(permission_result.association_scopes_entities) == 1
            assoc = permission_result.association_scopes_entities[0]
            assert assoc.scope_id.scope_type == "user"
            assert assoc.scope_id.scope_id == str(permission.user)
            assert assoc.object_id.entity_id == str(vfolder.id)

    def test_mixed_ownership_types(self, test_data):
        """Test handling vfolders with different ownership types."""
        user_vfolder: MockVFolderRow = test_data["vfolders"]["user_vfolder"]
        project_vfolder: MockVFolderRow = test_data["vfolders"]["project_vfolder"]

        # Convert user-owned vfolder
        user_result = vfolder_row_to_rbac_row(user_vfolder)
        user_assoc = user_result.association_scopes_entities[0]
        assert user_assoc.scope_id.scope_type == "user"
        assert user_assoc.scope_id.scope_id == str(user_vfolder.user)

        # Convert project-owned vfolder
        project_result = vfolder_row_to_rbac_row(project_vfolder)
        project_assoc = project_result.association_scopes_entities[0]
        assert project_assoc.scope_id.scope_type == "project"
        assert project_assoc.scope_id.scope_id == str(project_vfolder.group)
