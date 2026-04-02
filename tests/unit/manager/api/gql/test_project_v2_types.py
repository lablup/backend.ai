"""Unit tests for ProjectV2 GraphQL types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.group.response import (
    ProjectBasicInfo,
    ProjectLifecycleInfo,
    ProjectNode,
    ProjectOrganizationInfo,
    ProjectStorageInfo,
    VFolderHostPermissionEntry,
)
from ai.backend.common.dto.manager.v2.group.types import ProjectType
from ai.backend.manager.api.gql.project_v2.types import (
    ProjectTypeEnum,
    ProjectV2GQL,
    VFolderHostPermissionEnum,
)


def _make_project_node(
    *,
    project_id: uuid.UUID | None = None,
    name: str = "test-project",
    description: str | None = "Test project description",
    project_type: ProjectType = ProjectType.GENERAL,
    integration_name: str | None = None,
    domain_name: str = "default",
    resource_policy: str = "default-policy",
    allowed_vfolder_hosts: list[VFolderHostPermissionEntry] | None = None,
    is_active: bool | None = True,
    created_at: datetime | None = None,
    modified_at: datetime | None = None,
) -> ProjectNode:
    return ProjectNode(
        id=project_id or uuid.uuid4(),
        basic_info=ProjectBasicInfo(
            name=name,
            description=description,
            type=project_type,
            integration_name=integration_name,
        ),
        organization=ProjectOrganizationInfo(
            domain_name=domain_name,
            resource_policy=resource_policy,
        ),
        storage=ProjectStorageInfo(
            allowed_vfolder_hosts=allowed_vfolder_hosts or [],
        ),
        lifecycle=ProjectLifecycleInfo(
            is_active=is_active,
            created_at=created_at,
            modified_at=modified_at,
        ),
    )


class TestProjectV2GQL:
    """Tests for ProjectV2GQL type conversions."""

    def test_from_pydantic_basic_conversion(self) -> None:
        """Test basic ProjectNode to ProjectV2GQL conversion."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        modified = datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC)
        dto = _make_project_node(
            name="test-project",
            description="Test project description",
            integration_name="integration-123",
            domain_name="default",
            resource_policy="default-policy",
            is_active=True,
            created_at=created,
            modified_at=modified,
        )

        project_gql = ProjectV2GQL.from_pydantic(dto)

        # Verify basic info
        assert project_gql.basic_info.name == "test-project"
        assert project_gql.basic_info.description == "Test project description"
        assert project_gql.basic_info.type == ProjectTypeEnum.GENERAL
        assert project_gql.basic_info.integration_name == "integration-123"

        # Verify organization
        assert project_gql.organization.domain_name == "default"
        assert project_gql.organization.resource_policy == "default-policy"

        # Verify lifecycle
        assert project_gql.lifecycle.is_active is True
        assert project_gql.lifecycle.created_at == created
        assert project_gql.lifecycle.modified_at == modified

    def test_from_pydantic_project_type_conversion(self) -> None:
        """Test ProjectType to ProjectTypeEnum conversion."""
        for project_type, expected_enum in [
            (ProjectType.GENERAL, ProjectTypeEnum.GENERAL),
            (ProjectType.MODEL_STORE, ProjectTypeEnum.MODEL_STORE),
        ]:
            dto = _make_project_node(project_type=project_type)
            project_gql = ProjectV2GQL.from_pydantic(dto)
            assert project_gql.basic_info.type == expected_enum

    def test_from_pydantic_vfolder_hosts_conversion(self) -> None:
        """Test VFolderHostPermissionEntry list conversion."""
        # Empty hosts
        dto_empty = _make_project_node(allowed_vfolder_hosts=[])
        project_gql_empty = ProjectV2GQL.from_pydantic(dto_empty)
        assert len(project_gql_empty.storage.allowed_vfolder_hosts) == 0

        # Multiple hosts with permissions
        dto_with_hosts = _make_project_node(
            allowed_vfolder_hosts=[
                VFolderHostPermissionEntry(
                    host="default",
                    permissions=["create-vfolder", "modify-vfolder", "delete-vfolder"],
                ),
                VFolderHostPermissionEntry(
                    host="storage-01",
                    permissions=["create-vfolder", "upload-file", "download-file"],
                ),
            ]
        )

        project_gql_with_hosts = ProjectV2GQL.from_pydantic(dto_with_hosts)
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

    def test_from_pydantic_optional_fields(self) -> None:
        """Test handling of optional/nullable fields."""
        dto = _make_project_node(
            name="minimal-project",
            description=None,
            integration_name=None,
            is_active=None,
            created_at=None,
            modified_at=None,
        )

        project_gql = ProjectV2GQL.from_pydantic(dto)

        # Verify None values are preserved
        assert project_gql.basic_info.description is None
        assert project_gql.basic_info.integration_name is None
        assert project_gql.lifecycle.is_active is None
        assert project_gql.lifecycle.created_at is None
        assert project_gql.lifecycle.modified_at is None
