"""Test for vfolder RBAC migration module."""

import uuid

import pytest

from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migrate.vfolder import (
    ProjectVFolderData,
    UserVFolderData,
    VFolderPermissionData,
    map_project_vfolder_to_project_admin_role,
    map_project_vfolder_to_project_user_role,
    map_user_vfolder_to_user_role,
    map_vfolder_permission_data_to_user_role,
)


@pytest.fixture
def user_vfolder_data():
    """Create UserVFolderData for testing."""
    return UserVFolderData(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )


@pytest.fixture
def project_vfolder_data():
    """Create ProjectVFolderData for testing."""
    return ProjectVFolderData(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
    )


@pytest.fixture
def vfolder_permission_data():
    """Create VFolderPermissionData for testing."""
    return VFolderPermissionData(
        vfolder_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )


@pytest.fixture
def role_id():
    """Create a role ID for testing."""
    return uuid.uuid4()


class TestMapUserVFolderToUserRole:
    """Test map_user_vfolder_to_user_role function."""

    def test_basic_mapping(self, role_id, user_vfolder_data):
        """Test basic user vfolder mapping."""
        result = map_user_vfolder_to_user_role(role_id, user_vfolder_data)

        # Check scope permissions - should have all operations
        assert len(result.scope_permissions) == len(OperationType)

        for perm in result.scope_permissions:
            assert perm.role_id == role_id
            assert perm.scope_type == ScopeType.USER
            assert perm.scope_id == str(user_vfolder_data.user_id)
            assert perm.entity_type == EntityType.VFOLDER
            assert perm.operation in [str(op) for op in OperationType]

        # Check all operations are present
        operations = {perm.operation for perm in result.scope_permissions}
        expected_operations = {str(op) for op in OperationType}
        assert operations == expected_operations

        # Check association scopes entities
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.USER
        assert assoc.scope_id.scope_id == str(user_vfolder_data.user_id)
        assert assoc.object_id.entity_type == EntityType.VFOLDER
        assert assoc.object_id.entity_id == str(user_vfolder_data.id)

    def test_multiple_vfolders_same_user(self, role_id):
        """Test mapping multiple vfolders for the same user."""
        user_id = uuid.uuid4()
        vfolders = [
            UserVFolderData(id=uuid.uuid4(), user_id=user_id),
            UserVFolderData(id=uuid.uuid4(), user_id=user_id),
            UserVFolderData(id=uuid.uuid4(), user_id=user_id),
        ]

        results = []
        for vfolder in vfolders:
            result = map_user_vfolder_to_user_role(role_id, vfolder)
            results.append(result)

        # Each result should have the same scope but different object
        for i, result in enumerate(results):
            assert len(result.scope_permissions) == len(OperationType)
            assert result.association_scopes_entities[0].scope_id.scope_id == str(user_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolders[i].id)


class TestMapProjectVFolderToProjectAdminRole:
    """Test map_project_vfolder_to_project_admin_role function."""

    def test_admin_role_mapping(self, role_id, project_vfolder_data):
        """Test project vfolder mapping with admin role."""
        result = map_project_vfolder_to_project_admin_role(role_id, project_vfolder_data)

        # Admin should have all operations
        assert len(result.scope_permissions) == len(OperationType)

        for perm in result.scope_permissions:
            assert perm.role_id == role_id
            assert perm.scope_type == ScopeType.PROJECT
            assert perm.scope_id == str(project_vfolder_data.project_id)
            assert perm.entity_type == EntityType.VFOLDER

        # Check all operations are present
        operations = {perm.operation for perm in result.scope_permissions}
        expected_operations = {str(op) for op in OperationType}
        assert operations == expected_operations

        # Check association
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.PROJECT
        assert assoc.scope_id.scope_id == str(project_vfolder_data.project_id)
        assert assoc.object_id.entity_type == EntityType.VFOLDER
        assert assoc.object_id.entity_id == str(project_vfolder_data.id)

    def test_multiple_vfolders_same_project(self, role_id):
        """Test mapping multiple vfolders for the same project."""
        project_id = uuid.uuid4()
        vfolders = [
            ProjectVFolderData(id=uuid.uuid4(), project_id=project_id),
            ProjectVFolderData(id=uuid.uuid4(), project_id=project_id),
            ProjectVFolderData(id=uuid.uuid4(), project_id=project_id),
        ]

        results = []
        for vfolder in vfolders:
            result = map_project_vfolder_to_project_admin_role(role_id, vfolder)
            results.append(result)

        # Each result should have the same scope but different object
        for i, result in enumerate(results):
            assert len(result.scope_permissions) == len(OperationType)
            assert result.association_scopes_entities[0].scope_id.scope_id == str(project_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolders[i].id)


class TestMapProjectVFolderToProjectUserRole:
    """Test map_project_vfolder_to_project_user_role function."""

    def test_user_role_mapping(self, role_id, project_vfolder_data):
        """Test project vfolder mapping with user role."""
        result = map_project_vfolder_to_project_user_role(role_id, project_vfolder_data)

        # User should only have READ operation
        assert len(result.scope_permissions) == 1
        perm = result.scope_permissions[0]

        assert perm.role_id == role_id
        assert perm.scope_type == ScopeType.PROJECT
        assert perm.scope_id == str(project_vfolder_data.project_id)
        assert perm.entity_type == EntityType.VFOLDER
        assert perm.operation == OperationType.READ

        # Check association
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.PROJECT
        assert assoc.scope_id.scope_id == str(project_vfolder_data.project_id)
        assert assoc.object_id.entity_type == EntityType.VFOLDER
        assert assoc.object_id.entity_id == str(project_vfolder_data.id)

    def test_admin_vs_user_permissions(self, role_id, project_vfolder_data):
        """Test difference between admin and user permissions."""
        admin_result = map_project_vfolder_to_project_admin_role(role_id, project_vfolder_data)
        user_result = map_project_vfolder_to_project_user_role(role_id, project_vfolder_data)

        # Admin should have more permissions
        assert len(admin_result.scope_permissions) > len(user_result.scope_permissions)
        assert len(admin_result.scope_permissions) == len(OperationType)
        assert len(user_result.scope_permissions) == 1

        # Both should have same association
        assert admin_result.association_scopes_entities == user_result.association_scopes_entities


class TestMapVFolderPermissionDataToUserRole:
    """Test map_vfolder_permission_data_to_user_role function."""

    def test_basic_permission_mapping(self, role_id, vfolder_permission_data):
        """Test basic vfolder permission mapping."""
        result = map_vfolder_permission_data_to_user_role(role_id, vfolder_permission_data)

        # Should only have READ permission
        assert len(result.scope_permissions) == 1
        perm = result.scope_permissions[0]

        assert perm.role_id == role_id
        assert perm.scope_type == ScopeType.USER
        assert perm.scope_id == str(vfolder_permission_data.user_id)
        assert perm.entity_type == EntityType.VFOLDER
        assert perm.operation == OperationType.READ

        # Check association
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.USER
        assert assoc.scope_id.scope_id == str(vfolder_permission_data.user_id)
        assert assoc.object_id.entity_type == EntityType.VFOLDER
        assert assoc.object_id.entity_id == str(vfolder_permission_data.vfolder_id)

    def test_permission_is_read_only(self, role_id, vfolder_permission_data):
        """Test that vfolder permission mapping only grants READ access."""
        result = map_vfolder_permission_data_to_user_role(role_id, vfolder_permission_data)

        # Extract all operations
        operations = [perm.operation for perm in result.scope_permissions]

        # Should only contain READ operation
        assert operations == [OperationType.READ]

        # Verify other operations are NOT included
        assert OperationType.CREATE not in operations
        assert OperationType.UPDATE not in operations
        assert OperationType.SOFT_DELETE not in operations
        assert OperationType.HARD_DELETE not in operations
        assert OperationType.GRANT_ALL not in operations
        assert OperationType.GRANT_READ not in operations

    def test_multiple_permissions_same_user(self, role_id):
        """Test multiple vfolder permissions for the same user."""
        user_id = uuid.uuid4()
        vfolder_ids = [uuid.uuid4() for _ in range(3)]
        permissions = [
            VFolderPermissionData(vfolder_id=vfolder_id, user_id=user_id)
            for vfolder_id in vfolder_ids
        ]

        results = []
        for perm in permissions:
            result = map_vfolder_permission_data_to_user_role(role_id, perm)
            results.append(result)

        # All should have same user scope but different vfolders
        for i, result in enumerate(results):
            # Verify scope permissions
            assert len(result.scope_permissions) == 1
            scope_perm = result.scope_permissions[0]
            assert scope_perm.role_id == role_id
            assert scope_perm.scope_type == ScopeType.USER
            assert scope_perm.scope_id == str(user_id)
            assert scope_perm.entity_type == EntityType.VFOLDER
            assert scope_perm.operation == OperationType.READ

            # Verify associations
            assert len(result.association_scopes_entities) == 1
            assoc = result.association_scopes_entities[0]
            assert assoc.scope_id.scope_id == str(user_id)
            assert assoc.object_id.entity_id == str(vfolder_ids[i])

    def test_multiple_users_same_vfolder(self, role_id):
        """Test multiple users with permission to the same vfolder."""
        vfolder_id = uuid.uuid4()
        user_ids = [uuid.uuid4() for _ in range(3)]
        permissions = [
            VFolderPermissionData(vfolder_id=vfolder_id, user_id=user_id) for user_id in user_ids
        ]

        results = []
        for perm in permissions:
            result = map_vfolder_permission_data_to_user_role(role_id, perm)
            results.append(result)

        # All should have same vfolder but different user scopes
        for i, result in enumerate(results):
            # Verify scope permissions
            assert len(result.scope_permissions) == 1
            scope_perm = result.scope_permissions[0]
            assert scope_perm.role_id == role_id
            assert scope_perm.scope_type == ScopeType.USER
            assert scope_perm.scope_id == str(user_ids[i])
            assert scope_perm.entity_type == EntityType.VFOLDER
            assert scope_perm.operation == OperationType.READ

            # Verify associations
            assert len(result.association_scopes_entities) == 1
            assoc = result.association_scopes_entities[0]
            assert assoc.scope_id.scope_id == str(user_ids[i])
            assert assoc.object_id.entity_id == str(vfolder_id)

    def test_different_roles_same_permission(self):
        """Test that different roles can be used for the same vfolder permission."""
        vfolder_permission = VFolderPermissionData(
            vfolder_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )

        role_ids = [uuid.uuid4() for _ in range(3)]
        results = []

        for role_id in role_ids:
            result = map_vfolder_permission_data_to_user_role(role_id, vfolder_permission)
            results.append(result)

        # All results should have different role IDs but same permission structure
        for i, result in enumerate(results):
            assert result.scope_permissions[0].role_id == role_ids[i]
            assert result.scope_permissions[0].scope_id == str(vfolder_permission.user_id)
            assert result.scope_permissions[0].operation == OperationType.READ
            assert result.association_scopes_entities[0].object_id.entity_id == str(
                vfolder_permission.vfolder_id
            )


class TestComplexScenarios:
    """Test complex scenarios combining multiple mappings."""

    def test_user_owned_vfolder_with_shared_permissions(self, role_id):
        """Test scenario where a user owns a vfolder and shares it with others."""
        owner_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()
        shared_user_ids = [uuid.uuid4() for _ in range(3)]

        # Owner mapping (full permissions)
        owner_vfolder = UserVFolderData(id=vfolder_id, user_id=owner_id)
        owner_result = map_user_vfolder_to_user_role(role_id, owner_vfolder)

        # Shared user mappings (read-only permissions)
        shared_results = []
        for user_id in shared_user_ids:
            perm = VFolderPermissionData(vfolder_id=vfolder_id, user_id=user_id)
            result = map_vfolder_permission_data_to_user_role(role_id, perm)
            shared_results.append(result)

        # Owner should have all operations
        assert len(owner_result.scope_permissions) == len(OperationType)

        # Shared users should only have READ
        for result in shared_results:
            assert len(result.scope_permissions) == 1
            assert result.scope_permissions[0].operation == OperationType.READ

        # All should reference the same vfolder
        assert owner_result.association_scopes_entities[0].object_id.entity_id == str(vfolder_id)
        for result in shared_results:
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolder_id)

    def test_project_vfolder_permissions_hierarchy(self, role_id):
        """Test project vfolder with different permission levels."""
        project_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        # Project vfolder for admin
        project_vfolder = ProjectVFolderData(id=vfolder_id, project_id=project_id)
        admin_result = map_project_vfolder_to_project_admin_role(role_id, project_vfolder)

        # Same vfolder for user
        user_result = map_project_vfolder_to_project_user_role(role_id, project_vfolder)

        # External user with explicit permission
        external_user_id = uuid.uuid4()
        perm = VFolderPermissionData(vfolder_id=vfolder_id, user_id=external_user_id)
        external_result = map_vfolder_permission_data_to_user_role(role_id, perm)

        # Verify permission hierarchy
        admin_ops = {p.operation for p in admin_result.scope_permissions}
        user_ops = {p.operation for p in user_result.scope_permissions}
        external_ops = {p.operation for p in external_result.scope_permissions}

        assert OperationType.READ in admin_ops
        assert OperationType.READ in user_ops
        assert OperationType.READ in external_ops

    def test_data_class_properties(self):
        """Test data class creation and properties."""
        # UserVFolderData
        user_vfolder = UserVFolderData(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert isinstance(user_vfolder.id, uuid.UUID)
        assert isinstance(user_vfolder.user_id, uuid.UUID)

        # ProjectVFolderData
        project_vfolder = ProjectVFolderData(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
        )
        assert isinstance(project_vfolder.id, uuid.UUID)
        assert isinstance(project_vfolder.project_id, uuid.UUID)

        # VFolderPermissionData
        vfolder_permission = VFolderPermissionData(
            vfolder_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert isinstance(vfolder_permission.vfolder_id, uuid.UUID)
        assert isinstance(vfolder_permission.user_id, uuid.UUID)
