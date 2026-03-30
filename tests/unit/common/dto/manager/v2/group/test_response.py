"""Tests for ai.backend.common.dto.manager.v2.group.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.group.response import (
    DeleteProjectPayload,
    ProjectBasicInfo,
    ProjectLifecycleInfo,
    ProjectNode,
    ProjectOrganizationInfo,
    ProjectPayload,
    ProjectStorageInfo,
    PurgeProjectPayload,
    SearchProjectsPayload,
    VFolderHostPermissionEntry,
)
from ai.backend.common.dto.manager.v2.group.types import ProjectType


def make_project_node(project_id: uuid.UUID | None = None) -> ProjectNode:
    """Helper to create a valid ProjectNode for testing."""
    if project_id is None:
        project_id = uuid.uuid4()
    now = datetime.now(tz=UTC)
    return ProjectNode(
        id=project_id,
        basic_info=ProjectBasicInfo(
            name="test-project",
            description="Test project",
            type=ProjectType.GENERAL,
            integration_id=None,
        ),
        organization=ProjectOrganizationInfo(
            domain_name="default",
            resource_policy="default",
        ),
        storage=ProjectStorageInfo(
            allowed_vfolder_hosts=[
                VFolderHostPermissionEntry(
                    host="default",
                    permissions=["read", "write"],
                )
            ],
        ),
        lifecycle=ProjectLifecycleInfo(
            is_active=True,
            created_at=now,
            modified_at=now,
        ),
    )


class TestProjectBasicInfo:
    """Tests for ProjectBasicInfo sub-model."""

    def test_creation_with_required_fields(self) -> None:
        info = ProjectBasicInfo(name="project", type=ProjectType.GENERAL)
        assert info.name == "project"
        assert info.type == ProjectType.GENERAL
        assert info.description is None
        assert info.integration_id is None

    def test_creation_with_all_fields(self) -> None:
        info = ProjectBasicInfo(
            name="ml-store",
            description="ML model store",
            type=ProjectType.MODEL_STORE,
            integration_id="ext-789",
        )
        assert info.type == ProjectType.MODEL_STORE
        assert info.description == "ML model store"
        assert info.integration_id == "ext-789"

    def test_round_trip(self) -> None:
        info = ProjectBasicInfo(name="p", type=ProjectType.GENERAL, description="Desc")
        json_data = info.model_dump_json()
        restored = ProjectBasicInfo.model_validate_json(json_data)
        assert restored.name == "p"
        assert restored.type == ProjectType.GENERAL
        assert restored.description == "Desc"


class TestProjectOrganizationInfo:
    """Tests for ProjectOrganizationInfo sub-model."""

    def test_creation_with_required_fields(self) -> None:
        info = ProjectOrganizationInfo(domain_name="default", resource_policy="default")
        assert info.domain_name == "default"
        assert info.resource_policy == "default"

    def test_round_trip(self) -> None:
        info = ProjectOrganizationInfo(domain_name="prod", resource_policy="prod-policy")
        json_data = info.model_dump_json()
        restored = ProjectOrganizationInfo.model_validate_json(json_data)
        assert restored.domain_name == "prod"
        assert restored.resource_policy == "prod-policy"


class TestVFolderHostPermissionEntry:
    """Tests for VFolderHostPermissionEntry sub-model."""

    def test_creation_with_host_and_permissions(self) -> None:
        entry = VFolderHostPermissionEntry(host="storage-01", permissions=["read", "write"])
        assert entry.host == "storage-01"
        assert entry.permissions == ["read", "write"]

    def test_empty_permissions(self) -> None:
        entry = VFolderHostPermissionEntry(host="default", permissions=[])
        assert entry.permissions == []

    def test_round_trip(self) -> None:
        entry = VFolderHostPermissionEntry(host="nfs-01", permissions=["read"])
        json_data = entry.model_dump_json()
        restored = VFolderHostPermissionEntry.model_validate_json(json_data)
        assert restored.host == "nfs-01"
        assert restored.permissions == ["read"]


class TestProjectStorageInfo:
    """Tests for ProjectStorageInfo sub-model."""

    def test_empty_allowed_hosts(self) -> None:
        info = ProjectStorageInfo(allowed_vfolder_hosts=[])
        assert info.allowed_vfolder_hosts == []

    def test_with_host_entries(self) -> None:
        info = ProjectStorageInfo(
            allowed_vfolder_hosts=[
                VFolderHostPermissionEntry(host="default", permissions=["read", "write"]),
                VFolderHostPermissionEntry(host="nfs-01", permissions=["read"]),
            ]
        )
        assert len(info.allowed_vfolder_hosts) == 2
        assert info.allowed_vfolder_hosts[0].host == "default"

    def test_round_trip(self) -> None:
        info = ProjectStorageInfo(
            allowed_vfolder_hosts=[
                VFolderHostPermissionEntry(host="storage", permissions=["read"]),
            ]
        )
        json_data = info.model_dump_json()
        restored = ProjectStorageInfo.model_validate_json(json_data)
        assert len(restored.allowed_vfolder_hosts) == 1
        assert restored.allowed_vfolder_hosts[0].host == "storage"


class TestProjectLifecycleInfo:
    """Tests for ProjectLifecycleInfo sub-model."""

    def test_defaults_all_none(self) -> None:
        info = ProjectLifecycleInfo()
        assert info.is_active is None
        assert info.created_at is None
        assert info.modified_at is None

    def test_creation_with_values(self) -> None:
        now = datetime.now(tz=UTC)
        info = ProjectLifecycleInfo(is_active=True, created_at=now, modified_at=now)
        assert info.is_active is True

    def test_inactive_project(self) -> None:
        now = datetime.now(tz=UTC)
        info = ProjectLifecycleInfo(is_active=False, created_at=now, modified_at=now)
        assert info.is_active is False

    def test_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        info = ProjectLifecycleInfo(is_active=True, created_at=now, modified_at=now)
        json_data = info.model_dump_json()
        restored = ProjectLifecycleInfo.model_validate_json(json_data)
        assert restored.is_active is True
        assert restored.created_at is not None


class TestProjectNode:
    """Tests for ProjectNode model with nested sub-models."""

    def test_creation_with_all_nested_groups(self) -> None:
        project_id = uuid.uuid4()
        node = make_project_node(project_id)
        assert node.id == project_id
        assert node.basic_info.name == "test-project"
        assert node.basic_info.type == ProjectType.GENERAL
        assert node.organization.domain_name == "default"
        assert len(node.storage.allowed_vfolder_hosts) == 1
        assert node.lifecycle.is_active is True

    def test_id_is_uuid(self) -> None:
        node = make_project_node()
        assert isinstance(node.id, uuid.UUID)

    def test_nested_basic_info(self) -> None:
        node = make_project_node()
        assert node.basic_info.name == "test-project"
        assert node.basic_info.description == "Test project"

    def test_nested_organization_info(self) -> None:
        node = make_project_node()
        assert node.organization.domain_name == "default"
        assert node.organization.resource_policy == "default"

    def test_nested_storage_info_with_permissions(self) -> None:
        node = make_project_node()
        assert len(node.storage.allowed_vfolder_hosts) == 1
        entry = node.storage.allowed_vfolder_hosts[0]
        assert entry.host == "default"
        assert "read" in entry.permissions
        assert "write" in entry.permissions

    def test_nested_lifecycle_info(self) -> None:
        node = make_project_node()
        assert node.lifecycle.is_active is True
        assert node.lifecycle.created_at is not None

    def test_round_trip_serialization(self) -> None:
        project_id = uuid.uuid4()
        node = make_project_node(project_id)
        json_str = node.model_dump_json()
        restored = ProjectNode.model_validate_json(json_str)
        assert restored.id == project_id
        assert restored.basic_info.name == "test-project"
        assert restored.basic_info.type == ProjectType.GENERAL
        assert restored.organization.domain_name == "default"
        assert len(restored.storage.allowed_vfolder_hosts) == 1
        assert restored.lifecycle.is_active is True

    def test_serialized_json_has_nested_structure(self) -> None:
        node = make_project_node()
        data = json.loads(node.model_dump_json())
        assert "basic_info" in data
        assert "organization" in data
        assert "storage" in data
        assert "lifecycle" in data
        assert "allowed_vfolder_hosts" in data["storage"]
        assert "name" in data["basic_info"]


class TestProjectPayload:
    """Tests for ProjectPayload model."""

    def test_creation_with_project_node(self) -> None:
        node = make_project_node()
        payload = ProjectPayload(project=node)
        assert payload.project.basic_info.name == "test-project"

    def test_round_trip(self) -> None:
        project_id = uuid.uuid4()
        node = make_project_node(project_id)
        payload = ProjectPayload(project=node)
        json_str = payload.model_dump_json()
        restored = ProjectPayload.model_validate_json(json_str)
        assert restored.project.id == project_id
        assert restored.project.basic_info.name == "test-project"


class TestSearchProjectsPayload:
    """Tests for SearchProjectsPayload model."""

    def test_empty_items(self) -> None:
        payload = SearchProjectsPayload(
            items=[],
            pagination=PaginationInfo(total=0, offset=0, limit=20),
        )
        assert payload.items == []
        assert payload.pagination.total == 0

    def test_with_items(self) -> None:
        nodes = [make_project_node(), make_project_node()]
        payload = SearchProjectsPayload(
            items=nodes,
            pagination=PaginationInfo(total=2, offset=0, limit=10),
        )
        assert len(payload.items) == 2
        assert payload.pagination.total == 2

    def test_round_trip(self) -> None:
        project_id = uuid.uuid4()
        node = make_project_node(project_id)
        payload = SearchProjectsPayload(
            items=[node],
            pagination=PaginationInfo(total=1, offset=0, limit=10),
        )
        json_str = payload.model_dump_json()
        restored = SearchProjectsPayload.model_validate_json(json_str)
        assert len(restored.items) == 1
        assert restored.items[0].id == project_id
        assert restored.pagination.total == 1

    def test_vfolder_host_permissions_preserved_in_round_trip(self) -> None:
        node = make_project_node()
        payload = SearchProjectsPayload(
            items=[node],
            pagination=PaginationInfo(total=1, offset=0, limit=10),
        )
        json_str = payload.model_dump_json()
        restored = SearchProjectsPayload.model_validate_json(json_str)
        entry = restored.items[0].storage.allowed_vfolder_hosts[0]
        assert entry.host == "default"
        assert "read" in entry.permissions


class TestDeleteProjectPayload:
    """Tests for DeleteProjectPayload model."""

    def test_deleted_true(self) -> None:
        payload = DeleteProjectPayload(deleted=True)
        assert payload.deleted is True

    def test_deleted_false(self) -> None:
        payload = DeleteProjectPayload(deleted=False)
        assert payload.deleted is False

    def test_round_trip(self) -> None:
        payload = DeleteProjectPayload(deleted=True)
        json_str = payload.model_dump_json()
        restored = DeleteProjectPayload.model_validate_json(json_str)
        assert restored.deleted is True


class TestPurgeProjectPayload:
    """Tests for PurgeProjectPayload model."""

    def test_purged_true(self) -> None:
        payload = PurgeProjectPayload(purged=True)
        assert payload.purged is True

    def test_purged_false(self) -> None:
        payload = PurgeProjectPayload(purged=False)
        assert payload.purged is False

    def test_round_trip(self) -> None:
        payload = PurgeProjectPayload(purged=False)
        json_str = payload.model_dump_json()
        restored = PurgeProjectPayload.model_validate_json(json_str)
        assert restored.purged is False
