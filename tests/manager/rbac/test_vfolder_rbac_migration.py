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
    VFolderPermission,
    VFolderPermissionData,
    map_project_vfolder_to_project_admin_role,
    map_project_vfolder_to_project_user_role,
    map_user_vfolder_to_user_role,
    map_vfolder_permission_data_to_user_role,
    vfolder_mount_permission_to_operation,
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
        mount_permission=VFolderPermission.READ_ONLY,
    )


@pytest.fixture
def role_id():
    """Create a role ID for testing."""
    return uuid.uuid4()


class TestVFolderMountPermissionToOperation:
    """Test vfolder_mount_permission_to_operation mapping."""

    def test_read_only_permission(self):
        """Test READ_ONLY permission mapping."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.READ_ONLY]
        assert operations == [OperationType.READ]

    def test_read_write_permission(self):
        """Test READ_WRITE permission mapping."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.READ_WRITE]
        assert operations == [OperationType.READ, OperationType.UPDATE]

    def test_rw_delete_permission(self):
        """Test RW_DELETE permission mapping."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.RW_DELETE]
        assert operations == [
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        ]

    def test_owner_perm_permission(self):
        """Test OWNER_PERM permission mapping."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.OWNER_PERM]
        assert operations == [
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        ]
        # OWNER_PERM should be same as RW_DELETE
        assert operations == vfolder_mount_permission_to_operation[VFolderPermission.RW_DELETE]

    def test_all_permissions_are_mapped(self):
        """Test that all VFolderPermission enum values are mapped."""
        for perm in VFolderPermission:
            assert perm in vfolder_mount_permission_to_operation
            assert len(vfolder_mount_permission_to_operation[perm]) > 0


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
        for vfolder_data, result in zip(vfolders, results):
            assert len(result.scope_permissions) == len(OperationType)
            assert result.association_scopes_entities[0].scope_id.scope_id == str(user_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolder_data.id)


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
        for vfolder_data, result in zip(vfolders, results):
            assert len(result.scope_permissions) == len(OperationType)
            assert result.association_scopes_entities[0].scope_id.scope_id == str(project_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolder_data.id)


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

        assert len(result.object_permissions) == 1  # READ_ONLY has only READ operation
        perm = result.object_permissions[0]

        assert perm.role_id == role_id
        assert perm.entity_type == EntityType.VFOLDER
        assert perm.entity_id == str(vfolder_permission_data.vfolder_id)
        assert perm.operation == OperationType.READ

        # Check association
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.USER
        assert assoc.scope_id.scope_id == str(vfolder_permission_data.user_id)
        assert assoc.object_id.entity_type == EntityType.VFOLDER
        assert assoc.object_id.entity_id == str(vfolder_permission_data.vfolder_id)

        # Verify no scope permissions are set
        assert result.scope_permissions is None or len(result.scope_permissions) == 0

    def test_permission_mapping_by_mount_permission(self, role_id):
        """Test that vfolder permission mapping respects mount permissions."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Test READ_ONLY permission
        ro_perm = VFolderPermissionData(
            vfolder_id=vfolder_id,
            user_id=user_id,
            mount_permission=VFolderPermission.READ_ONLY,
        )
        ro_result = map_vfolder_permission_data_to_user_role(role_id, ro_perm)
        ro_operations = {perm.operation for perm in ro_result.object_permissions}
        assert ro_operations == {OperationType.READ}

        # Test READ_WRITE permission
        rw_perm = VFolderPermissionData(
            vfolder_id=vfolder_id,
            user_id=user_id,
            mount_permission=VFolderPermission.READ_WRITE,
        )
        rw_result = map_vfolder_permission_data_to_user_role(role_id, rw_perm)
        rw_operations = {perm.operation for perm in rw_result.object_permissions}
        assert rw_operations == {OperationType.READ, OperationType.UPDATE}

        # Test RW_DELETE permission
        wd_perm = VFolderPermissionData(
            vfolder_id=vfolder_id,
            user_id=user_id,
            mount_permission=VFolderPermission.RW_DELETE,
        )
        wd_result = map_vfolder_permission_data_to_user_role(role_id, wd_perm)
        wd_operations = {perm.operation for perm in wd_result.object_permissions}
        assert wd_operations == {
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        }

        # Test OWNER_PERM permission (should be same as RW_DELETE)
        owner_perm = VFolderPermissionData(
            vfolder_id=vfolder_id,
            user_id=user_id,
            mount_permission=VFolderPermission.OWNER_PERM,
        )
        owner_result = map_vfolder_permission_data_to_user_role(role_id, owner_perm)
        owner_operations = {perm.operation for perm in owner_result.object_permissions}
        assert owner_operations == wd_operations

    def test_multiple_permissions_same_user(self, role_id):
        """Test multiple vfolder permissions for the same user."""
        user_id = uuid.uuid4()
        vfolder_ids = [uuid.uuid4() for _ in range(3)]
        mount_perms = [
            VFolderPermission.READ_ONLY,
            VFolderPermission.READ_WRITE,
            VFolderPermission.RW_DELETE,
        ]
        permissions = [
            VFolderPermissionData(
                vfolder_id=vfolder_id,
                user_id=user_id,
                mount_permission=mount_perm,
            )
            for vfolder_id, mount_perm in zip(vfolder_ids, mount_perms)
        ]

        results = []
        for perm in permissions:
            result = map_vfolder_permission_data_to_user_role(role_id, perm)
            results.append(result)

        # Verify different permission levels
        for result, perm, vfolder_id in zip(results, permissions, vfolder_ids):
            # Verify object permissions match mount permission
            expected_ops = set(vfolder_mount_permission_to_operation[perm.mount_permission])
            actual_ops = {op.operation for op in result.object_permissions}
            assert actual_ops == expected_ops

            # Verify all permissions target the correct vfolder
            for obj_perm in result.object_permissions:
                assert obj_perm.entity_id == str(vfolder_id)
                assert obj_perm.role_id == role_id

            # Verify associations
            assert len(result.association_scopes_entities) == 1
            assoc = result.association_scopes_entities[0]
            assert assoc.scope_id.scope_id == str(user_id)
            assert assoc.object_id.entity_id == str(vfolder_id)

    def test_multiple_users_same_vfolder(self, role_id):
        """Test multiple users with permission to the same vfolder."""
        vfolder_id = uuid.uuid4()
        user_ids = [uuid.uuid4() for _ in range(3)]
        permissions = [
            VFolderPermissionData(
                vfolder_id=vfolder_id,
                user_id=user_id,
                mount_permission=VFolderPermission.READ_WRITE,
            )
            for user_id in user_ids
        ]

        results = []
        for perm in permissions:
            result = map_vfolder_permission_data_to_user_role(role_id, perm)
            results.append(result)

        # All should have same vfolder but different user scopes
        for user_id, result in zip(user_ids, results):
            # Verify object permissions
            assert len(result.object_permissions) == 2  # READ and UPDATE for READ_WRITE
            for obj_perm in result.object_permissions:
                assert obj_perm.role_id == role_id
                assert obj_perm.entity_type == EntityType.VFOLDER
                assert obj_perm.entity_id == str(vfolder_id)

            operations = {perm.operation for perm in result.object_permissions}
            assert operations == {OperationType.READ, OperationType.UPDATE}

            # Verify associations
            assert len(result.association_scopes_entities) == 1
            assoc = result.association_scopes_entities[0]
            assert assoc.scope_id.scope_id == str(user_id)
            assert assoc.object_id.entity_id == str(vfolder_id)

    def test_different_roles_same_permission(self):
        """Test that different roles can be used for the same vfolder permission."""
        vfolder_permission = VFolderPermissionData(
            vfolder_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            mount_permission=VFolderPermission.RW_DELETE,
        )

        role_ids = [uuid.uuid4() for _ in range(3)]
        results = []

        for role_id in role_ids:
            result = map_vfolder_permission_data_to_user_role(role_id, vfolder_permission)
            results.append(result)

        # All results should have different role IDs but same permission structure
        for role_id, result in zip(role_ids, results):
            # Each permission in the result should have the correct role_id
            for obj_perm in result.object_permissions:
                assert obj_perm.role_id == role_id
                assert obj_perm.entity_id == str(vfolder_permission.vfolder_id)

            # All should have same operations based on mount permission
            operations = {perm.operation for perm in result.object_permissions}
            expected_ops = set(vfolder_mount_permission_to_operation[VFolderPermission.RW_DELETE])
            assert operations == expected_ops

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

        # Shared user mappings (with different permission levels)
        shared_results = []
        mount_perms = [
            VFolderPermission.READ_ONLY,
            VFolderPermission.READ_WRITE,
            VFolderPermission.RW_DELETE,
        ]
        for user_id, mount_perm in zip(shared_user_ids, mount_perms):
            perm = VFolderPermissionData(
                vfolder_id=vfolder_id,
                user_id=user_id,
                mount_permission=mount_perm,
            )
            result = map_vfolder_permission_data_to_user_role(role_id, perm)
            shared_results.append(result)

        # Owner should have all operations
        assert len(owner_result.scope_permissions) == len(OperationType)

        # Shared users should have permissions based on mount permission
        expected_ops_list = [
            {OperationType.READ},
            {OperationType.READ, OperationType.UPDATE},
            {
                OperationType.READ,
                OperationType.UPDATE,
                OperationType.SOFT_DELETE,
                OperationType.HARD_DELETE,
            },
        ]
        for result, expected_ops in zip(shared_results, expected_ops_list):
            actual_ops = {perm.operation for perm in result.object_permissions}
            assert actual_ops == expected_ops

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
        perm = VFolderPermissionData(
            vfolder_id=vfolder_id,
            user_id=external_user_id,
            mount_permission=VFolderPermission.READ_ONLY,
        )
        external_result = map_vfolder_permission_data_to_user_role(role_id, perm)

        # Verify permission hierarchy
        admin_ops = {p.operation for p in admin_result.scope_permissions}
        user_ops = {p.operation for p in user_result.scope_permissions}
        external_ops = {p.operation for p in external_result.object_permissions}

        assert OperationType.READ in admin_ops
        assert OperationType.READ in user_ops
        assert OperationType.READ in external_ops
