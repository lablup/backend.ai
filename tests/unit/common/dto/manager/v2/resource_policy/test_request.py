"""Tests for ai.backend.common.dto.manager.v2.resource_policy.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.common import (
    ResourceSlotEntryInput,
    VFolderHostPermissionEntryInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
    DeleteKeypairResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    DeleteUserResourcePolicyInput,
    UpdateKeypairResourcePolicyInput,
    UpdateProjectResourcePolicyInput,
    UpdateUserResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.types import DefaultForUnspecified


class TestCreateKeypairResourcePolicyInput:
    """Tests for CreateKeypairResourcePolicyInput."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = CreateKeypairResourcePolicyInput(
            name="default",
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=[
                ResourceSlotEntryInput(resource_type="cpu", quantity="4"),
                ResourceSlotEntryInput(resource_type="mem", quantity="8589934592"),
            ],
            max_session_lifetime=3600,
            max_concurrent_sessions=10,
            max_concurrent_sftp_sessions=2,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts=[
                VFolderHostPermissionEntryInput(host="default", permissions=["mount-in-session"])
            ],
        )
        assert req.name == "default"
        assert req.default_for_unspecified == DefaultForUnspecified.LIMITED
        assert req.max_pending_session_count is None
        assert req.max_pending_session_resource_slots is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = CreateKeypairResourcePolicyInput(
            name="premium",
            default_for_unspecified=DefaultForUnspecified.UNLIMITED,
            total_resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="8")],
            max_session_lifetime=7200,
            max_concurrent_sessions=20,
            max_pending_session_count=5,
            max_pending_session_resource_slots=[
                ResourceSlotEntryInput(resource_type="cpu", quantity="2")
            ],
            max_concurrent_sftp_sessions=4,
            max_containers_per_session=2,
            idle_timeout=3600,
            allowed_vfolder_hosts=[
                VFolderHostPermissionEntryInput(host="default", permissions=["mount-in-session"]),
                VFolderHostPermissionEntryInput(host="nfs", permissions=["upload-file"]),
            ],
        )
        assert req.name == "premium"
        assert req.max_pending_session_count == 5
        assert (
            req.max_pending_session_resource_slots is not None
            and len(req.max_pending_session_resource_slots) == 1
        )

    def test_name_whitespace_is_stripped(self) -> None:
        req = CreateKeypairResourcePolicyInput(
            name="  default  ",
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=[],
            max_session_lifetime=3600,
            max_concurrent_sessions=10,
            max_concurrent_sftp_sessions=2,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts=[],
        )
        assert req.name == "default"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateKeypairResourcePolicyInput(
                name="",
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=[],
                max_session_lifetime=3600,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=2,
                max_containers_per_session=1,
                idle_timeout=1800,
                allowed_vfolder_hosts=[],
            )

    def test_name_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateKeypairResourcePolicyInput(
                name="a" * 257,
                default_for_unspecified=DefaultForUnspecified.LIMITED,
                total_resource_slots=[],
                max_session_lifetime=3600,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=2,
                max_containers_per_session=1,
                idle_timeout=1800,
                allowed_vfolder_hosts=[],
            )

    def test_round_trip(self) -> None:
        req = CreateKeypairResourcePolicyInput(
            name="default",
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="4")],
            max_session_lifetime=3600,
            max_concurrent_sessions=10,
            max_concurrent_sftp_sessions=2,
            max_containers_per_session=1,
            idle_timeout=1800,
            allowed_vfolder_hosts=[],
        )
        json_data = req.model_dump_json()
        restored = CreateKeypairResourcePolicyInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.default_for_unspecified == req.default_for_unspecified


class TestUpdateKeypairResourcePolicyInput:
    """Tests for UpdateKeypairResourcePolicyInput."""

    def test_all_none_fields_is_valid(self) -> None:
        req = UpdateKeypairResourcePolicyInput(
            default_for_unspecified=None,
            max_session_lifetime=None,
            max_concurrent_sessions=None,
            max_concurrent_sftp_sessions=None,
            max_containers_per_session=None,
            idle_timeout=None,
        )
        assert req.default_for_unspecified is None

    def test_default_sentinel_fields(self) -> None:
        req = UpdateKeypairResourcePolicyInput()
        assert req.total_resource_slots is SENTINEL
        assert isinstance(req.total_resource_slots, Sentinel)
        assert req.max_pending_session_count is SENTINEL
        assert req.max_pending_session_resource_slots is SENTINEL
        assert req.allowed_vfolder_hosts is SENTINEL

    def test_sentinel_signals_clear(self) -> None:
        req = UpdateKeypairResourcePolicyInput(total_resource_slots=SENTINEL)
        assert req.total_resource_slots is SENTINEL

    def test_none_means_no_change(self) -> None:
        req = UpdateKeypairResourcePolicyInput(total_resource_slots=None)
        assert req.total_resource_slots is None

    def test_update_specific_field(self) -> None:
        req = UpdateKeypairResourcePolicyInput(max_concurrent_sessions=20)
        assert req.max_concurrent_sessions == 20


class TestDeleteKeypairResourcePolicyInput:
    """Tests for DeleteKeypairResourcePolicyInput."""

    def test_valid_creation(self) -> None:
        req = DeleteKeypairResourcePolicyInput(name="default")
        assert req.name == "default"

    def test_missing_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteKeypairResourcePolicyInput.model_validate({})


class TestCreateUserResourcePolicyInput:
    """Tests for CreateUserResourcePolicyInput."""

    def test_valid_creation(self) -> None:
        req = CreateUserResourcePolicyInput(
            name="user-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
        assert req.name == "user-policy"
        assert req.max_vfolder_count == 10
        assert req.max_quota_scope_size == 1073741824

    def test_name_whitespace_stripped(self) -> None:
        req = CreateUserResourcePolicyInput(
            name="  user-policy  ",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
        assert req.name == "user-policy"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateUserResourcePolicyInput(
                name="",
                max_vfolder_count=10,
                max_quota_scope_size=1073741824,
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )

    def test_round_trip(self) -> None:
        req = CreateUserResourcePolicyInput(
            name="user-policy",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,
            max_session_count_per_model_session=5,
            max_customized_image_count=3,
        )
        json_data = req.model_dump_json()
        restored = CreateUserResourcePolicyInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.max_vfolder_count == req.max_vfolder_count


class TestUpdateUserResourcePolicyInput:
    """Tests for UpdateUserResourcePolicyInput."""

    def test_all_default_sentinel_fields(self) -> None:
        req = UpdateUserResourcePolicyInput()
        assert req.max_vfolder_count is SENTINEL
        assert req.max_quota_scope_size is SENTINEL

    def test_all_sentinel_fields_is_valid(self) -> None:
        req = UpdateUserResourcePolicyInput(
            max_vfolder_count=SENTINEL,
            max_quota_scope_size=SENTINEL,
            max_session_count_per_model_session=None,
            max_customized_image_count=None,
        )
        assert req.max_vfolder_count is SENTINEL

    def test_update_specific_field(self) -> None:
        req = UpdateUserResourcePolicyInput(max_session_count_per_model_session=10)
        assert req.max_session_count_per_model_session == 10


class TestDeleteUserResourcePolicyInput:
    """Tests for DeleteUserResourcePolicyInput."""

    def test_valid_creation(self) -> None:
        req = DeleteUserResourcePolicyInput(name="user-policy")
        assert req.name == "user-policy"

    def test_missing_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteUserResourcePolicyInput.model_validate({})


class TestCreateProjectResourcePolicyInput:
    """Tests for CreateProjectResourcePolicyInput."""

    def test_valid_creation(self) -> None:
        req = CreateProjectResourcePolicyInput(
            name="project-policy",
            max_vfolder_count=20,
            max_quota_scope_size=10737418240,
            max_network_count=5,
        )
        assert req.name == "project-policy"
        assert req.max_vfolder_count == 20
        assert req.max_network_count == 5

    def test_name_whitespace_stripped(self) -> None:
        req = CreateProjectResourcePolicyInput(
            name="  project-policy  ",
            max_vfolder_count=20,
            max_quota_scope_size=10737418240,
            max_network_count=5,
        )
        assert req.name == "project-policy"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateProjectResourcePolicyInput(
                name="",
                max_vfolder_count=20,
                max_quota_scope_size=10737418240,
                max_network_count=5,
            )

    def test_round_trip(self) -> None:
        req = CreateProjectResourcePolicyInput(
            name="project-policy",
            max_vfolder_count=20,
            max_quota_scope_size=10737418240,
            max_network_count=5,
        )
        json_data = req.model_dump_json()
        restored = CreateProjectResourcePolicyInput.model_validate_json(json_data)
        assert restored.name == req.name
        assert restored.max_vfolder_count == req.max_vfolder_count


class TestUpdateProjectResourcePolicyInput:
    """Tests for UpdateProjectResourcePolicyInput."""

    def test_all_default_sentinel_fields(self) -> None:
        req = UpdateProjectResourcePolicyInput()
        assert req.max_vfolder_count is SENTINEL
        assert req.max_quota_scope_size is SENTINEL

    def test_all_sentinel_fields_is_valid(self) -> None:
        req = UpdateProjectResourcePolicyInput(
            max_vfolder_count=SENTINEL,
            max_quota_scope_size=SENTINEL,
            max_network_count=None,
        )
        assert req.max_vfolder_count is SENTINEL

    def test_update_specific_field(self) -> None:
        req = UpdateProjectResourcePolicyInput(max_network_count=10)
        assert req.max_network_count == 10


class TestDeleteProjectResourcePolicyInput:
    """Tests for DeleteProjectResourcePolicyInput."""

    def test_valid_creation(self) -> None:
        req = DeleteProjectResourcePolicyInput(name="project-policy")
        assert req.name == "project-policy"

    def test_missing_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteProjectResourcePolicyInput.model_validate({})
