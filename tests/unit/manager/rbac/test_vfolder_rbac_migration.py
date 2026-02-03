"""Test for vfolder RBAC migration module."""

from ai.backend.manager.models.rbac_models.migration.enums import (
    OperationType,
    RoleSource,
)
from ai.backend.manager.models.rbac_models.migration.vfolder import (
    VFolderPermission,
    role_source_to_operation,
    vfolder_mount_permission_to_operation,
)


class TestVfolderMountPermissionToOperation:
    """Test vfolder_mount_permission_to_operation mapping."""

    def test_mapping_contains_all_permission_types(self) -> None:
        """Test that the mapping contains all expected VFolderPermission types."""
        expected_permissions = {
            VFolderPermission.READ_ONLY,
            VFolderPermission.READ_WRITE,
            VFolderPermission.RW_DELETE,
            VFolderPermission.OWNER_PERM,
        }

        assert set(vfolder_mount_permission_to_operation.keys()) == expected_permissions

    def test_read_only_permission_mapping(self) -> None:
        """Test READ_ONLY permission maps to READ operation only."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.READ_ONLY]

        assert len(operations) == 1
        assert operations == {OperationType.READ}

    def test_read_write_permission_mapping(self) -> None:
        """Test READ_WRITE permission maps to READ and UPDATE operations."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.READ_WRITE]

        assert len(operations) == 2
        assert operations == {OperationType.READ, OperationType.UPDATE}

    def test_rw_delete_permission_mapping(self) -> None:
        """Test RW_DELETE permission maps to full CRUD operations."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.RW_DELETE]

        assert len(operations) == 4
        assert operations == {
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        }

    def test_owner_permission_mapping(self) -> None:
        """Test OWNER_PERM permission maps to full CRUD operations."""
        operations = vfolder_mount_permission_to_operation[VFolderPermission.OWNER_PERM]

        assert len(operations) == 4
        assert operations == {
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        }

    def test_owner_and_rw_delete_are_equivalent(self) -> None:
        """Test that OWNER_PERM and RW_DELETE have the same operations."""
        owner_ops = vfolder_mount_permission_to_operation[VFolderPermission.OWNER_PERM]
        rw_delete_ops = vfolder_mount_permission_to_operation[VFolderPermission.RW_DELETE]

        assert owner_ops == rw_delete_ops


class TestRoleSourceToOperation:
    """Test role_source_to_operation mapping."""

    def test_mapping_contains_all_role_sources(self) -> None:
        """Test that the mapping contains all RoleSource types."""
        expected_sources = {RoleSource.SYSTEM, RoleSource.CUSTOM}
        assert set(role_source_to_operation.keys()) == expected_sources

    def test_system_role_maps_to_owner_operations(self) -> None:
        """Test that SYSTEM role source maps to owner operations."""
        operations = role_source_to_operation[RoleSource.SYSTEM]
        expected_operations = OperationType.owner_operations()

        assert operations == expected_operations

        # System role should get all operation types
        assert OperationType.CREATE in operations
        assert OperationType.READ in operations
        assert OperationType.UPDATE in operations
        assert OperationType.SOFT_DELETE in operations
        assert OperationType.HARD_DELETE in operations
        assert OperationType.GRANT_ALL in operations

    def test_custom_role_maps_to_member_operations(self) -> None:
        """Test that CUSTOM role source maps to member operations."""
        operations = role_source_to_operation[RoleSource.CUSTOM]
        expected_operations = OperationType.member_operations()

        assert operations == expected_operations

        # Custom role should only get READ operation
        assert operations == {OperationType.READ}
        assert len(operations) == 1

    def test_system_has_more_operations_than_custom(self) -> None:
        """Test that SYSTEM role has more operations than CUSTOM role."""
        system_ops = role_source_to_operation[RoleSource.SYSTEM]
        custom_ops = role_source_to_operation[RoleSource.CUSTOM]

        assert len(system_ops) > len(custom_ops)
        assert custom_ops.issubset(system_ops)
