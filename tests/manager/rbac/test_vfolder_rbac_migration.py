"""Test for vfolder RBAC migration module."""

import uuid

from ai.backend.manager.data.permission.types import (
    EntityType as OriginalEntityType,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as OriginalScopeType,
)
from ai.backend.manager.models.rbac_models.migration.enums import (
    OPERATIONS_FOR_CUSTOM_ROLE,
    OPERATIONS_FOR_SYSTEM_ROLE,
    EntityType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migration.vfolder import (
    RoleData,
    ScopeData,
    VFolderData,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionData,
    add_vfolder_scope_permissions_to_role,
    map_vfolder_entity_to_scope,
    map_vfolder_permission_data_to_scope,
)

PROJECT_RESOURCE_POLICY_NAME = "default"
USER_RESOURCE_POLICY_NAME = "default"


class TestAddVfolderScopePermissionsToRole:
    """Test add_vfolder_scope_permissions_to_role function."""

    def test_system_role_gets_all_operations(self):
        """Test that system-defined roles get all vfolder operations."""
        role = RoleData(
            id=uuid.uuid4(),
            source=RoleSource.SYSTEM,
        )
        scope = ScopeData(
            type=ScopeType.PROJECT,
            id=str(uuid.uuid4()),
        )

        result = add_vfolder_scope_permissions_to_role(role, scope)

        assert len(result.scope_permissions) == len(OPERATIONS_FOR_SYSTEM_ROLE)
        for perm in result.scope_permissions:
            assert perm.role_id == role.id
            assert perm.scope_type == scope.type.to_original()
            assert perm.scope_id == scope.id
            assert perm.entity_type == EntityType.VFOLDER.to_original()
            assert perm.operation in [op.to_original() for op in OPERATIONS_FOR_SYSTEM_ROLE]

    def test_custom_role_gets_limited_operations(self):
        """Test that custom-defined roles get limited vfolder operations."""
        role = RoleData(
            id=uuid.uuid4(),
            source=RoleSource.CUSTOM,
        )
        scope = ScopeData(
            type=ScopeType.USER,
            id=str(uuid.uuid4()),
        )

        result = add_vfolder_scope_permissions_to_role(role, scope)

        assert len(result.scope_permissions) == len(OPERATIONS_FOR_CUSTOM_ROLE)
        for perm in result.scope_permissions:
            assert perm.role_id == role.id
            assert perm.scope_type == scope.type.to_original()
            assert perm.scope_id == scope.id
            assert perm.entity_type == EntityType.VFOLDER.to_original()
            assert perm.operation in [op.to_original() for op in OPERATIONS_FOR_CUSTOM_ROLE]

    def test_different_scope_types(self):
        """Test function works with different scope types."""
        role = RoleData(
            id=uuid.uuid4(),
            source=RoleSource.SYSTEM,
        )
        scope_types = [ScopeType.USER, ScopeType.PROJECT, ScopeType.DOMAIN]

        for scope_type in scope_types:
            scope = ScopeData(
                type=scope_type,
                id=str(uuid.uuid4()),
            )
            result = add_vfolder_scope_permissions_to_role(role, scope)

            assert result.scope_permissions
            for perm in result.scope_permissions:
                assert perm.scope_type == scope_type.to_original()
                assert perm.scope_id == scope.id

    def test_no_association_entities_created(self):
        """Test that this function doesn't create association entities."""
        role = RoleData(
            id=uuid.uuid4(),
            source=RoleSource.SYSTEM,
        )
        scope = ScopeData(
            type=ScopeType.PROJECT,
            id=str(uuid.uuid4()),
        )

        result = add_vfolder_scope_permissions_to_role(role, scope)

        assert result.association_scopes_entities == []
        assert result.object_permissions == []


class TestMapVfolderEntityToScope:
    """Test map_vfolder_entity_to_scope function."""

    def test_user_owned_vfolder(self):
        """Test mapping for user-owned vfolder."""
        user_id = uuid.uuid4()
        vfolder = VFolderData(
            id=uuid.uuid4(),
            ownership_type=VFolderOwnershipType.USER,
            user_id=user_id,
            group_id=None,
        )

        result = map_vfolder_entity_to_scope(vfolder)

class TestMapUserVFolderToUserScope:
    """Test map_user_vfolder_to_user_scope function."""

    def test_basic_mapping(self, role_id, user_vfolder_data):
        """Test basic user vfolder mapping."""
        result = map_user_vfolder_to_user_scope(role_id, user_vfolder_data)

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

        assert assoc.scope_id.scope_type == OriginalScopeType.USER
        assert assoc.scope_id.scope_id == str(user_id)
        assert assoc.object_id.entity_type == OriginalEntityType.VFOLDER
        assert assoc.object_id.entity_id == str(vfolder.id)

        assert result.scope_permissions == []
        assert result.object_permissions == []

    def test_group_owned_vfolder(self):
        """Test mapping for group/project-owned vfolder."""
        group_id = uuid.uuid4()
        vfolder = VFolderData(
            id=uuid.uuid4(),
            ownership_type=VFolderOwnershipType.GROUP,
            user_id=None,
            group_id=group_id,
        )

        result = map_vfolder_entity_to_scope(vfolder)

        # Each result should have the same scope but different object
        for i, result in enumerate(results):
            assert len(result.scope_permissions) == len(OperationType)
            assert result.association_scopes_entities[0].scope_id.scope_id == str(user_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolders[i].id)


class TestMapProjectVFolderToProjectScope:
    """Test map_project_vfolder_to_project_scope function."""

    def test_admin_role_mapping(self, role_id, project_vfolder_data):
        """Test project vfolder mapping with admin role."""
        result = map_project_vfolder_to_project_scope(
            role_id, project_vfolder_data, is_admin_role=True
        )

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

        assert assoc.scope_id.scope_type == OriginalScopeType.PROJECT
        assert assoc.scope_id.scope_id == str(group_id)
        assert assoc.object_id.entity_type == OriginalEntityType.VFOLDER
        assert assoc.object_id.entity_id == str(vfolder.id)

        assert result.scope_permissions == []
        assert result.object_permissions == []

    def test_creates_only_association(self):
        """Test that function creates only association, no permissions."""
        vfolder = VFolderData(
            id=uuid.uuid4(),
            ownership_type=VFolderOwnershipType.USER,
            user_id=uuid.uuid4(),
            group_id=None,
        )

        result = map_vfolder_entity_to_scope(vfolder)

        assert result.association_scopes_entities is not None
        assert len(result.association_scopes_entities) == 1
        assert result.scope_permissions == []
        assert result.object_permissions == []


class TestMapVfolderPermissionDataToScope:
    """Test map_vfolder_permission_data_to_scope function."""

    def test_basic_permission_mapping(self):
        """Test basic vfolder permission to scope mapping."""
        user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()
        vfolder_permission = VFolderPermissionData(
            vfolder_id=vfolder_id,
            user_id=user_id,
            mount_permission=VFolderPermission.READ_ONLY,
        )

        result = map_vfolder_permission_data_to_scope(vfolder_permission)

        assert perm.role_id == role_id
        assert perm.scope_type == ScopeType.PROJECT
        assert perm.scope_id == str(project_vfolder_data.project_id)
        assert perm.entity_type == EntityType.VFOLDER
        assert perm.operation == OperationType.READ

        # Check association (same as admin)
        assert len(result.association_scopes_entities) == 1
        assoc = result.association_scopes_entities[0]
        assert assoc.scope_id.scope_type == ScopeType.PROJECT
        assert assoc.scope_id.scope_id == str(project_vfolder_data.project_id)
        assert assoc.object_id.entity_type == EntityType.VFOLDER
        assert assoc.object_id.entity_id == str(project_vfolder_data.id)

        assert assoc.scope_id.scope_type == OriginalScopeType.USER
        assert assoc.scope_id.scope_id == str(user_id)
        assert assoc.object_id.entity_type == OriginalEntityType.VFOLDER
        assert assoc.object_id.entity_id == str(vfolder_id)

    def test_always_creates_user_scope(self):
        """Test that function always creates USER scope type."""
        vfolder_permission = VFolderPermissionData(
            vfolder_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            mount_permission=VFolderPermission.READ_ONLY,
        )

        result = map_vfolder_permission_data_to_scope(vfolder_permission)

        assert result.association_scopes_entities[0].scope_id.scope_type == OriginalScopeType.USER

    def test_no_permissions_created(self):
        """Test that function doesn't create any permissions."""
        vfolder_permission = VFolderPermissionData(
            vfolder_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            mount_permission=VFolderPermission.READ_ONLY,
        )

        result = map_vfolder_permission_data_to_scope(vfolder_permission)

        assert result.scope_permissions == []
        assert result.object_permissions == []

    def test_multiple_permissions_same_user(self):
        """Test multiple vfolder permissions for the same user."""
        user_id = uuid.uuid4()
        vfolder_ids = [uuid.uuid4() for _ in range(3)]

        results = []
        for vfolder_id in vfolder_ids:
            vfolder_permission = VFolderPermissionData(
                vfolder_id=vfolder_id,
                user_id=user_id,
                mount_permission=VFolderPermission.READ_ONLY,
            )
            result = map_vfolder_permission_data_to_scope(vfolder_permission)
            results.append(result)

        for result, vfolder_id in zip(results, vfolder_ids):
            assert result.association_scopes_entities[0].scope_id.scope_id == str(user_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolder_id)

    def test_multiple_users_same_vfolder(self):
        """Test multiple users with permission to the same vfolder."""
        vfolder_id = uuid.uuid4()
        user_ids = [uuid.uuid4() for _ in range(3)]

        results = []
        for user_id in user_ids:
            vfolder_permission = VFolderPermissionData(
                vfolder_id=vfolder_id,
                user_id=user_id,
                mount_permission=VFolderPermission.READ_ONLY,
            )
            result = map_vfolder_permission_data_to_scope(vfolder_permission)
            results.append(result)

        for result, user_id in zip(results, user_ids):
            assert result.association_scopes_entities[0].scope_id.scope_id == str(user_id)
            assert result.association_scopes_entities[0].object_id.entity_id == str(vfolder_id)


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple functions."""

    def test_role_with_vfolder_scope_permissions(self):
        """Test creating a role with vfolder scope permissions."""
        # Create a system role with project scope
        role = RoleData(
            id=uuid.uuid4(),
            source=RoleSource.SYSTEM,
        )
        scope = ScopeData(
            type=ScopeType.PROJECT,
            id=str(uuid.uuid4()),
        )

        # Add vfolder permissions to the role
        permissions_result = add_vfolder_scope_permissions_to_role(role, scope)

        # Create a project vfolder
        vfolder = VFolderData(
            id=uuid.uuid4(),
            ownership_type=VFolderOwnershipType.GROUP,
            user_id=None,
            group_id=uuid.UUID(scope.id),
        )

        # Map vfolder to scope
        vfolder_result = map_vfolder_entity_to_scope(vfolder)

        # Verify the role has permissions and vfolder has association
        assert permissions_result.scope_permissions
        assert vfolder_result.association_scopes_entities

        # Both should reference the same scope
        for perm in permissions_result.scope_permissions:
            assert perm.scope_id == scope.id
        assert vfolder_result.association_scopes_entities[0].scope_id.scope_id == scope.id

    def test_user_vfolder_with_shared_permissions(self):
        """Test user vfolder with shared permissions to other users."""
        owner_id = uuid.uuid4()
        shared_user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        # Owner's vfolder
        owner_vfolder = VFolderData(
            id=vfolder_id,
            ownership_type=VFolderOwnershipType.USER,
            user_id=owner_id,
            group_id=None,
        )

        # Map owner's vfolder
        owner_result = map_vfolder_entity_to_scope(owner_vfolder)

        # Shared permission for another user
        shared_permission = VFolderPermissionData(
            vfolder_id=vfolder_id,
            user_id=shared_user_id,
            mount_permission=VFolderPermission.READ_ONLY,
        )

        # Map shared permission
        shared_result = map_vfolder_permission_data_to_scope(shared_permission)

        # Both should reference the same vfolder but different users
        assert owner_result.association_scopes_entities[0].object_id.entity_id == str(vfolder_id)
        assert shared_result.association_scopes_entities[0].object_id.entity_id == str(vfolder_id)

        assert owner_result.association_scopes_entities[0].scope_id.scope_id == str(owner_id)
        assert shared_result.association_scopes_entities[0].scope_id.scope_id == str(shared_user_id)

    def test_custom_role_limited_permissions(self):
        """Test that custom roles get limited permissions."""
        custom_role = RoleData(
            id=uuid.uuid4(),
            source=RoleSource.CUSTOM,
        )
        system_role = RoleData(
            id=uuid.uuid4(),
            source=RoleSource.SYSTEM,
        )
        scope = ScopeData(
            type=ScopeType.DOMAIN,
            id=str(uuid.uuid4()),
        )

        custom_result = add_vfolder_scope_permissions_to_role(custom_role, scope)
        system_result = add_vfolder_scope_permissions_to_role(system_role, scope)

        # Custom role should have fewer permissions
        assert len(custom_result.scope_permissions) < len(system_result.scope_permissions)
        assert len(custom_result.scope_permissions) == len(OPERATIONS_FOR_CUSTOM_ROLE)
        assert len(system_result.scope_permissions) == len(OPERATIONS_FOR_SYSTEM_ROLE)

        # Custom role should only have READ operation
        custom_operations = {perm.operation for perm in custom_result.scope_permissions}
        assert custom_operations == {op.to_original() for op in OPERATIONS_FOR_CUSTOM_ROLE}