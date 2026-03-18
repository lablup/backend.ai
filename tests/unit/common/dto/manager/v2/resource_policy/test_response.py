"""Tests for ai.backend.common.dto.manager.v2.resource_policy.response module."""

from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateKeypairResourcePolicyPayload,
    CreateProjectResourcePolicyPayload,
    CreateUserResourcePolicyPayload,
    DeleteKeypairResourcePolicyPayload,
    DeleteProjectResourcePolicyPayload,
    DeleteUserResourcePolicyPayload,
    KeypairResourcePolicyNode,
    ProjectResourcePolicyNode,
    UpdateKeypairResourcePolicyPayload,
    UpdateProjectResourcePolicyPayload,
    UpdateUserResourcePolicyPayload,
    UserResourcePolicyNode,
)
from ai.backend.common.dto.manager.v2.resource_policy.types import DefaultForUnspecified


def _make_keypair_policy_node(name: str = "default") -> KeypairResourcePolicyNode:
    return KeypairResourcePolicyNode(
        name=name,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        default_for_unspecified=DefaultForUnspecified.LIMITED,
        total_resource_slots={"cpu": "4", "mem": "8g"},
        max_session_lifetime=3600,
        max_concurrent_sessions=10,
        max_pending_session_count=None,
        max_pending_session_resource_slots=None,
        max_concurrent_sftp_sessions=2,
        max_containers_per_session=1,
        idle_timeout=1800,
        allowed_vfolder_hosts={"default": "rw"},
    )


def _make_user_policy_node(name: str = "user-policy") -> UserResourcePolicyNode:
    return UserResourcePolicyNode(
        name=name,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        max_vfolder_count=10,
        max_quota_scope_size=1073741824,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
    )


def _make_project_policy_node(name: str = "project-policy") -> ProjectResourcePolicyNode:
    return ProjectResourcePolicyNode(
        name=name,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        max_vfolder_count=20,
        max_quota_scope_size=10737418240,
        max_network_count=5,
    )


class TestKeypairResourcePolicyNode:
    """Tests for KeypairResourcePolicyNode model."""

    def test_valid_creation(self) -> None:
        node = _make_keypair_policy_node()
        assert node.name == "default"
        assert node.default_for_unspecified == DefaultForUnspecified.LIMITED
        assert node.max_concurrent_sessions == 10
        assert node.max_pending_session_count is None

    def test_valid_creation_without_created_at(self) -> None:
        node = KeypairResourcePolicyNode(
            name="default",
            default_for_unspecified=DefaultForUnspecified.UNLIMITED,
            total_resource_slots={},
            max_session_lifetime=3600,
            max_concurrent_sessions=10,
            max_concurrent_sftp_sessions=2,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts={},
        )
        assert node.created_at is None

    def test_serializes_correctly(self) -> None:
        node = _make_keypair_policy_node()
        data = node.model_dump()
        assert "name" in data
        assert "default_for_unspecified" in data
        assert "total_resource_slots" in data

    def test_round_trip(self) -> None:
        node = _make_keypair_policy_node()
        json_data = node.model_dump_json()
        restored = KeypairResourcePolicyNode.model_validate_json(json_data)
        assert restored.name == node.name
        assert restored.default_for_unspecified == node.default_for_unspecified
        assert restored.max_concurrent_sessions == node.max_concurrent_sessions


class TestCreateKeypairResourcePolicyPayload:
    """Tests for CreateKeypairResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        node = _make_keypair_policy_node()
        payload = CreateKeypairResourcePolicyPayload(keypair_resource_policy=node)
        assert payload.keypair_resource_policy.name == "default"

    def test_round_trip(self) -> None:
        node = _make_keypair_policy_node()
        payload = CreateKeypairResourcePolicyPayload(keypair_resource_policy=node)
        json_data = payload.model_dump_json()
        restored = CreateKeypairResourcePolicyPayload.model_validate_json(json_data)
        assert restored.keypair_resource_policy.name == payload.keypair_resource_policy.name


class TestUpdateKeypairResourcePolicyPayload:
    """Tests for UpdateKeypairResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        node = _make_keypair_policy_node()
        payload = UpdateKeypairResourcePolicyPayload(keypair_resource_policy=node)
        assert payload.keypair_resource_policy.name == "default"


class TestDeleteKeypairResourcePolicyPayload:
    """Tests for DeleteKeypairResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        payload = DeleteKeypairResourcePolicyPayload(name="default")
        assert payload.name == "default"

    def test_round_trip(self) -> None:
        payload = DeleteKeypairResourcePolicyPayload(name="default")
        json_data = payload.model_dump_json()
        restored = DeleteKeypairResourcePolicyPayload.model_validate_json(json_data)
        assert restored.name == payload.name


class TestUserResourcePolicyNode:
    """Tests for UserResourcePolicyNode model."""

    def test_valid_creation(self) -> None:
        node = _make_user_policy_node()
        assert node.name == "user-policy"
        assert node.max_vfolder_count == 10
        assert node.max_quota_scope_size == 1073741824
        assert node.max_session_count_per_model_session == 5
        assert node.max_customized_image_count == 3

    def test_round_trip(self) -> None:
        node = _make_user_policy_node()
        json_data = node.model_dump_json()
        restored = UserResourcePolicyNode.model_validate_json(json_data)
        assert restored.name == node.name
        assert restored.max_vfolder_count == node.max_vfolder_count


class TestCreateUserResourcePolicyPayload:
    """Tests for CreateUserResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        node = _make_user_policy_node()
        payload = CreateUserResourcePolicyPayload(user_resource_policy=node)
        assert payload.user_resource_policy.name == "user-policy"

    def test_round_trip(self) -> None:
        node = _make_user_policy_node()
        payload = CreateUserResourcePolicyPayload(user_resource_policy=node)
        json_data = payload.model_dump_json()
        restored = CreateUserResourcePolicyPayload.model_validate_json(json_data)
        assert restored.user_resource_policy.name == payload.user_resource_policy.name


class TestUpdateUserResourcePolicyPayload:
    """Tests for UpdateUserResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        node = _make_user_policy_node()
        payload = UpdateUserResourcePolicyPayload(user_resource_policy=node)
        assert payload.user_resource_policy.name == "user-policy"


class TestDeleteUserResourcePolicyPayload:
    """Tests for DeleteUserResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        payload = DeleteUserResourcePolicyPayload(name="user-policy")
        assert payload.name == "user-policy"


class TestProjectResourcePolicyNode:
    """Tests for ProjectResourcePolicyNode model."""

    def test_valid_creation(self) -> None:
        node = _make_project_policy_node()
        assert node.name == "project-policy"
        assert node.max_vfolder_count == 20
        assert node.max_quota_scope_size == 10737418240
        assert node.max_network_count == 5

    def test_round_trip(self) -> None:
        node = _make_project_policy_node()
        json_data = node.model_dump_json()
        restored = ProjectResourcePolicyNode.model_validate_json(json_data)
        assert restored.name == node.name
        assert restored.max_network_count == node.max_network_count


class TestCreateProjectResourcePolicyPayload:
    """Tests for CreateProjectResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        node = _make_project_policy_node()
        payload = CreateProjectResourcePolicyPayload(project_resource_policy=node)
        assert payload.project_resource_policy.name == "project-policy"

    def test_round_trip(self) -> None:
        node = _make_project_policy_node()
        payload = CreateProjectResourcePolicyPayload(project_resource_policy=node)
        json_data = payload.model_dump_json()
        restored = CreateProjectResourcePolicyPayload.model_validate_json(json_data)
        assert restored.project_resource_policy.name == payload.project_resource_policy.name


class TestUpdateProjectResourcePolicyPayload:
    """Tests for UpdateProjectResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        node = _make_project_policy_node()
        payload = UpdateProjectResourcePolicyPayload(project_resource_policy=node)
        assert payload.project_resource_policy.name == "project-policy"


class TestDeleteProjectResourcePolicyPayload:
    """Tests for DeleteProjectResourcePolicyPayload."""

    def test_valid_creation(self) -> None:
        payload = DeleteProjectResourcePolicyPayload(name="project-policy")
        assert payload.name == "project-policy"

    def test_round_trip(self) -> None:
        payload = DeleteProjectResourcePolicyPayload(name="project-policy")
        json_data = payload.model_dump_json()
        restored = DeleteProjectResourcePolicyPayload.model_validate_json(json_data)
        assert restored.name == payload.name
