"""Tests for CredentialData dict conversion matching legacy Core query output."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.auth.types import (
    CredentialData,
    KeypairDataForCredential,
    KeypairResourcePolicyDataForCredential,
    UserDataForCredential,
    UserResourcePolicyDataForCredential,
)
from ai.backend.manager.data.user.types import UserRole, UserStatus


@pytest.fixture
def user_rp() -> UserResourcePolicyDataForCredential:
    return UserResourcePolicyDataForCredential(
        name="user-policy",
        created_at=datetime.now(UTC),
        max_vfolder_count=10,
        max_quota_scope_size=-1,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
    )


@pytest.fixture
def keypair_rp() -> KeypairResourcePolicyDataForCredential:
    return KeypairResourcePolicyDataForCredential(
        name="keypair-policy",
        created_at=datetime.now(UTC),
        default_for_unspecified=DefaultForUnspecified.LIMITED,
        total_resource_slots=ResourceSlot({}),
        max_session_lifetime=0,
        max_concurrent_sessions=10,
        max_pending_session_count=None,
        max_pending_session_resource_slots=None,
        max_concurrent_sftp_sessions=2,
        max_containers_per_session=5,
        idle_timeout=3600,
        allowed_vfolder_hosts=VFolderHostPermissionMap({}),
    )


@pytest.fixture
def user_data(user_rp: UserResourcePolicyDataForCredential) -> UserDataForCredential:
    return UserDataForCredential(
        uuid=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        need_password_change=False,
        password_changed_at=datetime.now(UTC),
        full_name="Test User",
        status=UserStatus.ACTIVE,
        status_info="OK",
        modified_at=datetime.now(UTC),
        domain_name="default",
        role=UserRole.USER,
        allowed_client_ip=None,
        totp_key=None,
        totp_activated=False,
        totp_activated_at=None,
        resource_policy_name="user-policy",
        sudo_session_enabled=False,
        main_access_key="AKTEST123",
        integration_id=None,
        container_uid=None,
        container_main_gid=None,
        container_gids=None,
        resource_policy=user_rp,
    )


@pytest.fixture
def keypair_data(
    user_data: UserDataForCredential,
    keypair_rp: KeypairResourcePolicyDataForCredential,
) -> KeypairDataForCredential:
    return KeypairDataForCredential(
        user_id="test@example.com",
        access_key="AKTEST123",
        secret_key="secret_key_value",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(UTC),
        modified_at=datetime.now(UTC),
        last_used=None,
        rate_limit=1000,
        num_queries=0,
        ssh_public_key=None,
        ssh_private_key=None,
        user=user_data.uuid,
        resource_policy_name="keypair-policy",
        dotfiles=b"\x90",
        bootstrap_script="",
        resource_policy=keypair_rp,
    )


@pytest.fixture
def credential(
    user_data: UserDataForCredential,
    keypair_data: KeypairDataForCredential,
) -> CredentialData:
    return CredentialData(user=user_data, keypair=keypair_data)


class TestCredentialDataProperties:
    def test_secret_key(self, credential: CredentialData) -> None:
        assert credential.secret_key == "secret_key_value"

    def test_is_admin_false(self, credential: CredentialData) -> None:
        assert credential.is_admin is False

    def test_is_admin_true(
        self, user_data: UserDataForCredential, keypair_data: KeypairDataForCredential
    ) -> None:
        cred = CredentialData(user=user_data, keypair=replace(keypair_data, is_admin=True))
        assert cred.is_admin is True

    def test_is_superadmin_false(self, credential: CredentialData) -> None:
        assert credential.is_superadmin is False

    def test_is_superadmin_true(
        self, user_data: UserDataForCredential, keypair_data: KeypairDataForCredential
    ) -> None:
        cred = CredentialData(
            user=replace(user_data, role=UserRole.SUPERADMIN), keypair=keypair_data
        )
        assert cred.is_superadmin is True


class TestToKeypairDict:
    def test_excludes_secret_key(self, credential: CredentialData) -> None:
        assert "secret_key" not in credential.to_keypair_dict()

    def test_includes_keypair_fields(self, credential: CredentialData) -> None:
        result = credential.to_keypair_dict()
        assert result["access_key"] == "AKTEST123"
        assert result["user_id"] == "test@example.com"
        assert result["is_active"] is True
        assert result["rate_limit"] == 1000

    def test_includes_nested_resource_policy(self, credential: CredentialData) -> None:
        rp = credential.to_keypair_dict()["resource_policy"]
        assert rp["name"] == "keypair-policy"
        assert rp["max_concurrent_sessions"] == 10
        assert rp["idle_timeout"] == 3600


class TestToUserDict:
    def test_excludes_sensitive_fields(self, credential: CredentialData) -> None:
        result = credential.to_user_dict()
        assert "password" not in result
        assert "description" not in result
        assert "created_at" not in result

    def test_includes_user_fields(self, credential: CredentialData) -> None:
        result = credential.to_user_dict()
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert result["domain_name"] == "default"

    def test_id_from_keypair_user(self, credential: CredentialData) -> None:
        result = credential.to_user_dict()
        assert result["id"] == credential.keypair.user

    def test_includes_nested_resource_policy(self, credential: CredentialData) -> None:
        rp = credential.to_user_dict()["resource_policy"]
        assert rp["name"] == "user-policy"
        assert rp["max_vfolder_count"] == 10

    def test_role_enum_comparison(
        self, user_data: UserDataForCredential, keypair_data: KeypairDataForCredential
    ) -> None:
        cred = CredentialData(user=replace(user_data, role=UserRole.ADMIN), keypair=keypair_data)
        assert cred.to_user_dict()["role"] == "admin"

    def test_status_enum_comparison(
        self, user_data: UserDataForCredential, keypair_data: KeypairDataForCredential
    ) -> None:
        cred = CredentialData(
            user=replace(user_data, status=UserStatus.INACTIVE), keypair=keypair_data
        )
        assert cred.to_user_dict()["status"] == "inactive"
