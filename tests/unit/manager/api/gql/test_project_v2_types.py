"""Unit tests for ProjectV2 GraphQL types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.types import ResourceSlot, VFolderHostPermission, VFolderHostPermissionMap
from ai.backend.manager.api.gql.project_v2.types import (
    ProjectV2GQL,
    ProjectV2TypeEnum,
    VFolderHostPermissionEnum,
)
from ai.backend.manager.data.group.types import GroupData, ProjectType


class TestProjectV2GQL:
    """Tests for ProjectV2GQL type conversions."""

    def test_from_data_basic_conversion(self) -> None:
        """Test basic GroupData to ProjectV2GQL conversion."""
        # Create sample GroupData
        data = GroupData(
            id=uuid.uuid4(),
            name="test-project",
            description="Test project description",
            is_active=True,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            modified_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
            integration_id="integration-123",
            domain_name="default",
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            dotfiles=b"",
            resource_policy="default-policy",
            type=ProjectType.GENERAL,
            container_registry=None,
        )

        # Convert to GraphQL type
        project_gql = ProjectV2GQL.from_data(data)

        # Verify basic info
        assert project_gql.basic_info.name == "test-project"
        assert project_gql.basic_info.description == "Test project description"
        assert project_gql.basic_info.type == ProjectV2TypeEnum.GENERAL
        assert project_gql.basic_info.integration_id == "integration-123"

        # Verify organization
        assert project_gql.organization.domain_name == "default"
        assert project_gql.organization.resource_policy == "default-policy"

        # Verify lifecycle
        assert project_gql.lifecycle.is_active is True
        assert project_gql.lifecycle.created_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert project_gql.lifecycle.modified_at == datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC)

    def test_from_data_project_type_conversion(self) -> None:
        """Test ProjectType to ProjectV2TypeEnum conversion."""
        for project_type, expected_enum in [
            (ProjectType.GENERAL, ProjectV2TypeEnum.GENERAL),
            (ProjectType.MODEL_STORE, ProjectV2TypeEnum.MODEL_STORE),
        ]:
            data = GroupData(
                id=uuid.uuid4(),
                name="test",
                description=None,
                is_active=True,
                created_at=None,
                modified_at=None,
                integration_id=None,
                domain_name="default",
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                dotfiles=b"",
                resource_policy="default",
                type=project_type,
                container_registry=None,
            )

            project_gql = ProjectV2GQL.from_data(data)
            assert project_gql.basic_info.type == expected_enum

    def test_from_data_vfolder_hosts_conversion(self) -> None:
        """Test VFolderHostPermissionMap to list conversion."""
        # Empty hosts
        data_empty = GroupData(
            id=uuid.uuid4(),
            name="test",
            description=None,
            is_active=True,
            created_at=None,
            modified_at=None,
            integration_id=None,
            domain_name="default",
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            dotfiles=b"",
            resource_policy="default",
            type=ProjectType.GENERAL,
            container_registry=None,
        )

        project_gql_empty = ProjectV2GQL.from_data(data_empty)
        assert len(project_gql_empty.storage.allowed_vfolder_hosts) == 0

        # Multiple hosts with permissions
        data_with_hosts = GroupData(
            id=uuid.uuid4(),
            name="test",
            description=None,
            is_active=True,
            created_at=None,
            modified_at=None,
            integration_id=None,
            domain_name="default",
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap({
                "default": {
                    VFolderHostPermission.CREATE,
                    VFolderHostPermission.MODIFY,
                    VFolderHostPermission.DELETE,
                },
                "storage-01": {
                    VFolderHostPermission.CREATE,
                    VFolderHostPermission.UPLOAD_FILE,
                    VFolderHostPermission.DOWNLOAD_FILE,
                },
            }),
            dotfiles=b"",
            resource_policy="default",
            type=ProjectType.GENERAL,
            container_registry=None,
        )

        project_gql_with_hosts = ProjectV2GQL.from_data(data_with_hosts)
        assert len(project_gql_with_hosts.storage.allowed_vfolder_hosts) == 2

        # Verify host entries
        host_dict = {
            entry.host: entry.permissions
            for entry in project_gql_with_hosts.storage.allowed_vfolder_hosts
        }
        assert "default" in host_dict
        assert "storage-01" in host_dict

        # Verify permissions conversion
        default_perms = set(host_dict["default"])
        assert VFolderHostPermissionEnum.CREATE_VFOLDER in default_perms
        assert VFolderHostPermissionEnum.MODIFY_VFOLDER in default_perms
        assert VFolderHostPermissionEnum.DELETE_VFOLDER in default_perms

        storage_01_perms = set(host_dict["storage-01"])
        assert VFolderHostPermissionEnum.CREATE_VFOLDER in storage_01_perms
        assert VFolderHostPermissionEnum.UPLOAD_FILE in storage_01_perms
        assert VFolderHostPermissionEnum.DOWNLOAD_FILE in storage_01_perms

    def test_from_data_optional_fields(self) -> None:
        """Test handling of optional/nullable fields."""
        data = GroupData(
            id=uuid.uuid4(),
            name="minimal-project",
            description=None,  # None description
            is_active=None,  # None is_active
            created_at=None,  # None created_at
            modified_at=None,  # None modified_at
            integration_id=None,  # None integration_id
            domain_name="default",
            total_resource_slots=ResourceSlot(),
            allowed_vfolder_hosts=VFolderHostPermissionMap(),
            dotfiles=b"",
            resource_policy="default",
            type=ProjectType.GENERAL,
            container_registry=None,
        )

        project_gql = ProjectV2GQL.from_data(data)

        # Verify None values are preserved
        assert project_gql.basic_info.description is None
        assert project_gql.basic_info.integration_id is None
        assert project_gql.lifecycle.is_active is None
        assert project_gql.lifecycle.created_at is None
        assert project_gql.lifecycle.modified_at is None
