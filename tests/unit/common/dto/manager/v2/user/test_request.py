"""Tests for ai.backend.common.dto.manager.v2.user.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.user.request import (
    CreateUserInput,
    DeleteUserInput,
    PurgeUserInput,
    PurgeUserV2Input,
    PurgeUserV2Options,
    SearchUsersRequest,
    UpdateUserInput,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.types import (
    OrderDirection,
    UserOrderField,
    UserRole,
    UserRoleFilter,
    UserStatus,
    UserStatusFilter,
)


class TestCreateUserInput:
    """Tests for CreateUserInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = CreateUserInput(
            email="user@example.com",
            username="testuser",
            password="secret",
            domain_name="default",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        assert req.email == "user@example.com"
        assert req.username == "testuser"
        assert req.password == "secret"
        assert req.domain_name == "default"
        assert req.status == UserStatus.ACTIVE
        assert req.role == UserRole.USER

    def test_default_values(self) -> None:
        req = CreateUserInput(
            email="user@example.com",
            username="testuser",
            password="secret",
            domain_name="default",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        assert req.need_password_change is False
        assert req.full_name is None
        assert req.description is None
        assert req.group_ids is None
        assert req.allowed_client_ip is None
        assert req.totp_activated is False
        assert req.resource_policy == "default"
        assert req.sudo_session_enabled is False
        assert req.container_uid is None
        assert req.container_main_gid is None
        assert req.container_gids is None
        assert req.integration_name is None

    def test_valid_creation_with_all_fields(self) -> None:
        group_id = uuid.uuid4()
        req = CreateUserInput(
            email="admin@example.com",
            username="adminuser",
            password="secret123",
            domain_name="test-domain",
            need_password_change=True,
            status=UserStatus.BEFORE_VERIFICATION,
            role=UserRole.ADMIN,
            full_name="Admin User",
            description="An admin account",
            group_ids=[group_id],
            allowed_client_ip=["192.168.1.0/24"],
            totp_activated=True,
            resource_policy="admin-policy",
            sudo_session_enabled=True,
            container_uid=1000,
            container_main_gid=1000,
            container_gids=[100, 200],
            integration_name="ext-abc",
        )
        assert req.full_name == "Admin User"
        assert req.description == "An admin account"
        assert req.group_ids == [group_id]
        assert req.allowed_client_ip == ["192.168.1.0/24"]
        assert req.container_uid == 1000
        assert req.container_main_gid == 1000
        assert req.container_gids == [100, 200]
        assert req.integration_name == "ext-abc"

    def test_missing_required_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateUserInput.model_validate({
                "username": "user",
                "password": "secret",
                "domain_name": "default",
                "status": "active",
                "role": "user",
            })

    def test_missing_required_username_raises(self) -> None:
        with pytest.raises(ValidationError):
            CreateUserInput.model_validate({
                "email": "user@example.com",
                "password": "secret",
                "domain_name": "default",
                "status": "active",
                "role": "user",
            })

    def test_status_from_string(self) -> None:
        req = CreateUserInput.model_validate({
            "email": "u@e.com",
            "username": "u",
            "password": "p",
            "domain_name": "d",
            "status": "inactive",
            "role": "user",
        })
        assert req.status == UserStatus.INACTIVE

    def test_role_from_string(self) -> None:
        req = CreateUserInput.model_validate({
            "email": "u@e.com",
            "username": "u",
            "password": "p",
            "domain_name": "d",
            "status": "active",
            "role": "superadmin",
        })
        assert req.role == UserRole.SUPERADMIN

    def test_round_trip_serialization(self) -> None:
        req = CreateUserInput(
            email="user@example.com",
            username="testuser",
            password="secret",
            domain_name="default",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        json_data = req.model_dump_json()
        restored = CreateUserInput.model_validate_json(json_data)
        assert restored.email == req.email
        assert restored.username == req.username
        assert restored.status == req.status
        assert restored.role == req.role


class TestUpdateUserInput:
    """Tests for UpdateUserInput model with SENTINEL fields."""

    def test_empty_update_has_sentinel_defaults(self) -> None:
        req = UpdateUserInput()
        assert req.full_name is SENTINEL
        assert isinstance(req.full_name, Sentinel)
        assert req.description is SENTINEL
        assert isinstance(req.description, Sentinel)
        assert req.group_ids is SENTINEL
        assert req.allowed_client_ip is SENTINEL
        assert req.main_access_key is SENTINEL
        assert req.container_uid is SENTINEL
        assert req.container_main_gid is SENTINEL
        assert req.container_gids is SENTINEL
        assert req.integration_name is SENTINEL

    def test_non_sentinel_fields_default_to_none(self) -> None:
        req = UpdateUserInput()
        assert req.username is None
        assert req.password is None
        assert req.status is None
        assert req.role is None
        assert req.domain_name is None
        assert req.need_password_change is None
        assert req.resource_policy is None
        assert req.sudo_session_enabled is None

    def test_explicit_none_full_name_means_clear(self) -> None:
        req = UpdateUserInput(full_name=None)
        assert req.full_name is None

    def test_explicit_sentinel_full_name(self) -> None:
        req = UpdateUserInput(full_name=SENTINEL)
        assert req.full_name is SENTINEL

    def test_string_full_name_update(self) -> None:
        req = UpdateUserInput(full_name="New Name")
        assert req.full_name == "New Name"

    def test_none_description_means_clear(self) -> None:
        req = UpdateUserInput(description=None)
        assert req.description is None

    def test_string_description_update(self) -> None:
        req = UpdateUserInput(description="New description")
        assert req.description == "New description"

    def test_status_update(self) -> None:
        req = UpdateUserInput(status=UserStatus.INACTIVE)
        assert req.status == UserStatus.INACTIVE

    def test_role_update(self) -> None:
        req = UpdateUserInput(role=UserRole.ADMIN)
        assert req.role == UserRole.ADMIN

    def test_group_ids_none_clears(self) -> None:
        req = UpdateUserInput(group_ids=None)
        assert req.group_ids is None

    def test_group_ids_with_list(self) -> None:
        gid = uuid.uuid4()
        req = UpdateUserInput(group_ids=[gid])
        assert req.group_ids == [gid]

    def test_container_uid_none_clears(self) -> None:
        req = UpdateUserInput(container_uid=None)
        assert req.container_uid is None

    def test_container_uid_with_value(self) -> None:
        req = UpdateUserInput(container_uid=1000)
        assert req.container_uid == 1000

    def test_integration_name_sentinel_default(self) -> None:
        req = UpdateUserInput()
        assert req.integration_name is SENTINEL

    def test_integration_name_none_clears(self) -> None:
        req = UpdateUserInput(integration_name=None)
        assert req.integration_name is None

    def test_integration_name_with_value(self) -> None:
        req = UpdateUserInput(integration_name="ext-system")
        assert req.integration_name == "ext-system"

    def test_integration_name_max_length_rejects_over_512(self) -> None:
        with pytest.raises(ValidationError, match="integration_name"):
            UpdateUserInput(integration_name="x" * 513)

    def test_integration_name_max_length_accepts_exactly_512(self) -> None:
        req = UpdateUserInput(integration_name="x" * 512)
        assert req.integration_name == "x" * 512

    def test_round_trip_with_none_fields(self) -> None:
        req = UpdateUserInput(
            username="newname",
            full_name=None,
            description=None,
            status=UserStatus.ACTIVE,
        )
        json_data = req.model_dump_json()
        restored = UpdateUserInput.model_validate_json(json_data)
        assert restored.username == "newname"
        assert restored.full_name is None
        assert restored.description is None
        assert restored.status == UserStatus.ACTIVE


class TestDeleteUserInput:
    """Tests for DeleteUserInput model."""

    def test_valid_creation_with_uuid(self) -> None:
        user_id = uuid.uuid4()
        req = DeleteUserInput(user_id=user_id)
        assert req.user_id == user_id

    def test_valid_creation_from_uuid_string(self) -> None:
        user_id = uuid.uuid4()
        req = DeleteUserInput.model_validate({"user_id": str(user_id)})
        assert req.user_id == user_id

    def test_invalid_uuid_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteUserInput.model_validate({"user_id": "not-a-uuid"})

    def test_missing_user_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            DeleteUserInput.model_validate({})

    def test_round_trip(self) -> None:
        user_id = uuid.uuid4()
        req = DeleteUserInput(user_id=user_id)
        json_data = req.model_dump_json()
        restored = DeleteUserInput.model_validate_json(json_data)
        assert restored.user_id == user_id


class TestPurgeUserInput:
    """Tests for PurgeUserInput model."""

    def test_valid_creation_with_uuid(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserInput(user_id=user_id)
        assert req.user_id == user_id

    def test_default_flags_are_false(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserInput(user_id=user_id)
        assert req.purge_shared_vfolders is False
        assert req.delegate_endpoint_ownership is False

    def test_all_fields(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserInput(
            user_id=user_id,
            purge_shared_vfolders=True,
            delegate_endpoint_ownership=True,
        )
        assert req.purge_shared_vfolders is True
        assert req.delegate_endpoint_ownership is True

    def test_round_trip(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserInput(user_id=user_id, purge_shared_vfolders=True)
        json_data = req.model_dump_json()
        restored = PurgeUserInput.model_validate_json(json_data)
        assert restored.user_id == user_id
        assert restored.purge_shared_vfolders is True


class TestPurgeUserV2Options:
    """Tests for PurgeUserV2Options model."""

    def test_default_values_are_false(self) -> None:
        opts = PurgeUserV2Options()
        assert opts.purge_shared_vfolders is False
        assert opts.delegate_endpoint_ownership is False

    def test_purge_shared_vfolders_true(self) -> None:
        opts = PurgeUserV2Options(purge_shared_vfolders=True)
        assert opts.purge_shared_vfolders is True
        assert opts.delegate_endpoint_ownership is False

    def test_delegate_endpoint_ownership_true(self) -> None:
        opts = PurgeUserV2Options(delegate_endpoint_ownership=True)
        assert opts.purge_shared_vfolders is False
        assert opts.delegate_endpoint_ownership is True

    def test_both_flags_true(self) -> None:
        opts = PurgeUserV2Options(purge_shared_vfolders=True, delegate_endpoint_ownership=True)
        assert opts.purge_shared_vfolders is True
        assert opts.delegate_endpoint_ownership is True

    def test_round_trip(self) -> None:
        opts = PurgeUserV2Options(purge_shared_vfolders=True, delegate_endpoint_ownership=False)
        json_data = opts.model_dump_json()
        restored = PurgeUserV2Options.model_validate_json(json_data)
        assert restored.purge_shared_vfolders is True
        assert restored.delegate_endpoint_ownership is False

    def test_from_dict(self) -> None:
        opts = PurgeUserV2Options.model_validate({
            "purge_shared_vfolders": True,
            "delegate_endpoint_ownership": True,
        })
        assert opts.purge_shared_vfolders is True
        assert opts.delegate_endpoint_ownership is True


class TestPurgeUserV2Input:
    """Tests for PurgeUserV2Input model with and without options."""

    def test_valid_creation_with_only_user_id(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserV2Input(user_id=user_id)
        assert req.user_id == user_id
        assert req.options is None

    def test_options_defaults_to_none(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserV2Input(user_id=user_id)
        assert req.options is None

    def test_with_options_purge_shared_vfolders(self) -> None:
        user_id = uuid.uuid4()
        opts = PurgeUserV2Options(purge_shared_vfolders=True)
        req = PurgeUserV2Input(user_id=user_id, options=opts)
        assert req.options is not None
        assert req.options.purge_shared_vfolders is True
        assert req.options.delegate_endpoint_ownership is False

    def test_with_options_delegate_endpoint_ownership(self) -> None:
        user_id = uuid.uuid4()
        opts = PurgeUserV2Options(delegate_endpoint_ownership=True)
        req = PurgeUserV2Input(user_id=user_id, options=opts)
        assert req.options is not None
        assert req.options.purge_shared_vfolders is False
        assert req.options.delegate_endpoint_ownership is True

    def test_with_explicit_null_options(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserV2Input(user_id=user_id, options=None)
        assert req.options is None

    def test_missing_user_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            PurgeUserV2Input.model_validate({})

    def test_invalid_user_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            PurgeUserV2Input.model_validate({"user_id": "not-a-uuid"})

    def test_round_trip_without_options(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserV2Input(user_id=user_id)
        json_data = req.model_dump_json()
        restored = PurgeUserV2Input.model_validate_json(json_data)
        assert restored.user_id == user_id
        assert restored.options is None

    def test_round_trip_with_options(self) -> None:
        user_id = uuid.uuid4()
        opts = PurgeUserV2Options(purge_shared_vfolders=True, delegate_endpoint_ownership=True)
        req = PurgeUserV2Input(user_id=user_id, options=opts)
        json_data = req.model_dump_json()
        restored = PurgeUserV2Input.model_validate_json(json_data)
        assert restored.user_id == user_id
        assert restored.options is not None
        assert restored.options.purge_shared_vfolders is True
        assert restored.options.delegate_endpoint_ownership is True

    def test_from_dict_with_options(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserV2Input.model_validate({
            "user_id": str(user_id),
            "options": {
                "purge_shared_vfolders": True,
                "delegate_endpoint_ownership": False,
            },
        })
        assert req.user_id == user_id
        assert req.options is not None
        assert req.options.purge_shared_vfolders is True
        assert req.options.delegate_endpoint_ownership is False

    def test_from_dict_without_options(self) -> None:
        user_id = uuid.uuid4()
        req = PurgeUserV2Input.model_validate({"user_id": str(user_id)})
        assert req.user_id == user_id
        assert req.options is None


class TestUserFilter:
    """Tests for UserFilter model."""

    def test_empty_filter(self) -> None:
        f = UserFilter()
        assert f.uuid is None
        assert f.email is None
        assert f.username is None
        assert f.domain_name is None
        assert f.integration_name is None
        assert f.status is None
        assert f.role is None

    def test_integration_name_filter(self) -> None:
        f = UserFilter(
            integration_name=StringFilter(equals="k8s-user"),
        )
        assert f.integration_name is not None
        assert f.integration_name.equals == "k8s-user"

    def test_integration_name_filter_defaults_to_none(self) -> None:
        f = UserFilter(email=StringFilter(contains="test"))
        assert f.integration_name is None

    def test_status_filter(self) -> None:
        f = UserFilter(status=UserStatusFilter(in_=[UserStatus.ACTIVE, UserStatus.INACTIVE]))
        assert f.status is not None
        assert f.status.in_ == [UserStatus.ACTIVE, UserStatus.INACTIVE]

    def test_role_filter(self) -> None:
        f = UserFilter(role=UserRoleFilter(in_=[UserRole.ADMIN, UserRole.SUPERADMIN]))
        assert f.role is not None
        assert f.role.in_ == [UserRole.ADMIN, UserRole.SUPERADMIN]


class TestUserOrder:
    """Tests for UserOrder model."""

    def test_valid_order(self) -> None:
        order = UserOrder(field=UserOrderField.EMAIL)
        assert order.field == UserOrderField.EMAIL
        assert order.direction == OrderDirection.ASC

    def test_explicit_direction(self) -> None:
        order = UserOrder(field=UserOrderField.CREATED_AT, direction=OrderDirection.DESC)
        assert order.direction == OrderDirection.DESC

    def test_round_trip(self) -> None:
        order = UserOrder(field=UserOrderField.USERNAME, direction=OrderDirection.DESC)
        json_data = order.model_dump_json()
        restored = UserOrder.model_validate_json(json_data)
        assert restored.field == UserOrderField.USERNAME
        assert restored.direction == OrderDirection.DESC


class TestSearchUsersRequest:
    """Tests for SearchUsersRequest model."""

    def test_defaults(self) -> None:
        req = SearchUsersRequest()
        assert req.filter is None
        assert req.order is None
        assert req.offset == 0

    def test_limit_default_is_positive(self) -> None:
        req = SearchUsersRequest()
        assert req.limit >= 1

    def test_limit_too_small_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchUsersRequest(limit=0)

    def test_offset_negative_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchUsersRequest(offset=-1)

    def test_with_filter_and_order(self) -> None:
        req = SearchUsersRequest(
            filter=UserFilter(status=UserStatusFilter(equals=UserStatus.ACTIVE)),
            order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.ASC)],
            limit=10,
            offset=5,
        )
        assert req.filter is not None
        assert req.filter.status is not None
        assert req.filter.status.equals == UserStatus.ACTIVE
        assert req.order is not None
        assert len(req.order) == 1
        assert req.limit == 10
        assert req.offset == 5

    def test_round_trip(self) -> None:
        req = SearchUsersRequest(
            filter=UserFilter(role=UserRoleFilter(equals=UserRole.ADMIN)),
            limit=20,
            offset=0,
        )
        json_data = req.model_dump_json()
        restored = SearchUsersRequest.model_validate_json(json_data)
        assert restored.filter is not None
        assert restored.filter.role is not None
        assert restored.filter.role.equals == UserRole.ADMIN
        assert restored.limit == 20
