"""
Tests for user API adapter classes.
Tests conversion from DTO objects to repository Querier objects,
updater building, and data-to-DTO conversion.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.user import (
    OrderDirection,
    SearchUsersRequest,
    UpdateUserRequest,
    UserDTO,
    UserFilter,
    UserOrder,
    UserOrderField,
)
from ai.backend.common.dto.manager.user.types import UserRole as UserRoleDTO
from ai.backend.common.dto.manager.user.types import UserStatus as UserStatusDTO
from ai.backend.manager.api.user.adapter import UserAdapter
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.repositories.base import OffsetPagination
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec


class TestUserAdapterQuerier:
    """Test cases for UserAdapter.build_querier"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, and default limit"""
        request = SearchUsersRequest()
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 0
        assert len(querier.orders) == 0
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 50
        assert querier.pagination.offset == 0

    def test_uuid_equals_filter(self) -> None:
        """Test UUID equals filter"""
        user_uuid = uuid4()
        request = SearchUsersRequest(filter=UserFilter(uuid=UUIDFilter(equals=user_uuid)))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_uuid_in_filter(self) -> None:
        """Test UUID in filter (list of UUIDs)"""
        uuids = [uuid4(), uuid4(), uuid4()]
        request = SearchUsersRequest(filter=UserFilter(uuid=UUIDFilter(in_=uuids)))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_email_equals_filter(self) -> None:
        """Test email equals filter (case-sensitive)"""
        request = SearchUsersRequest(
            filter=UserFilter(email=StringFilter(equals="user@example.com"))
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_email_contains_filter(self) -> None:
        """Test email contains filter (case-sensitive)"""
        request = SearchUsersRequest(filter=UserFilter(email=StringFilter(contains="example")))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_email_contains_case_insensitive_filter(self) -> None:
        """Test email contains filter (case-insensitive)"""
        request = SearchUsersRequest(filter=UserFilter(email=StringFilter(i_contains="EXAMPLE")))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_username_equals_filter(self) -> None:
        """Test username equals filter"""
        request = SearchUsersRequest(filter=UserFilter(username=StringFilter(equals="testuser")))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_username_contains_filter(self) -> None:
        """Test username contains filter"""
        request = SearchUsersRequest(filter=UserFilter(username=StringFilter(contains="test")))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_domain_name_equals_filter(self) -> None:
        """Test domain_name equals filter"""
        request = SearchUsersRequest(filter=UserFilter(domain_name=StringFilter(equals="default")))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_status_filter(self) -> None:
        """Test status filter with list of statuses"""
        request = SearchUsersRequest(
            filter=UserFilter(status=[UserStatusDTO.ACTIVE, UserStatusDTO.INACTIVE])
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_role_filter(self) -> None:
        """Test role filter with list of roles"""
        request = SearchUsersRequest(filter=UserFilter(role=[UserRoleDTO.ADMIN, UserRoleDTO.USER]))
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        request = SearchUsersRequest(
            filter=UserFilter(
                email=StringFilter(contains="example"),
                status=[UserStatusDTO.ACTIVE],
                role=[UserRoleDTO.USER],
            )
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 3
        for condition in querier.conditions:
            assert condition() is not None

    def test_order_by_created_at_asc(self) -> None:
        """Test ordering by created_at ascending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.CREATED_AT, direction=OrderDirection.ASC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_desc(self) -> None:
        """Test ordering by created_at descending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.CREATED_AT, direction=OrderDirection.DESC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_modified_at_asc(self) -> None:
        """Test ordering by modified_at ascending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.MODIFIED_AT, direction=OrderDirection.ASC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_modified_at_desc(self) -> None:
        """Test ordering by modified_at descending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.MODIFIED_AT, direction=OrderDirection.DESC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_username_asc(self) -> None:
        """Test ordering by username ascending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.USERNAME, direction=OrderDirection.ASC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_username_desc(self) -> None:
        """Test ordering by username descending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.USERNAME, direction=OrderDirection.DESC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_email_asc(self) -> None:
        """Test ordering by email ascending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.ASC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_email_desc(self) -> None:
        """Test ordering by email descending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.DESC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_status_asc(self) -> None:
        """Test ordering by status ascending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.STATUS, direction=OrderDirection.ASC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_status_desc(self) -> None:
        """Test ordering by status descending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.STATUS, direction=OrderDirection.DESC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_domain_name_asc(self) -> None:
        """Test ordering by domain_name ascending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.DOMAIN_NAME, direction=OrderDirection.ASC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_domain_name_desc(self) -> None:
        """Test ordering by domain_name descending"""
        request = SearchUsersRequest(
            order=[UserOrder(field=UserOrderField.DOMAIN_NAME, direction=OrderDirection.DESC)]
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_pagination(self) -> None:
        """Test pagination parameters"""
        request = SearchUsersRequest(limit=10, offset=5)
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        request = SearchUsersRequest(
            filter=UserFilter(
                email=StringFilter(contains="example"),
                status=[UserStatusDTO.ACTIVE],
            ),
            order=[
                UserOrder(field=UserOrderField.CREATED_AT, direction=OrderDirection.DESC),
                UserOrder(field=UserOrderField.USERNAME, direction=OrderDirection.ASC),
            ],
            limit=20,
            offset=10,
        )
        adapter = UserAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 2
        assert len(querier.orders) == 2
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10


class TestUserAdapterUpdater:
    """Test cases for UserAdapter.build_updater"""

    def test_build_updater_all_fields(self) -> None:
        """Test building updater with all fields set"""
        request = UpdateUserRequest(
            username="newuser",
            need_password_change=True,
            full_name="New User",
            description="A new user",
            status=UserStatusDTO.ACTIVE,
            role=UserRoleDTO.ADMIN,
            domain_name="new-domain",
            allowed_client_ip=["192.168.1.1"],
            totp_activated=True,
            resource_policy="default",
            sudo_session_enabled=True,
            main_access_key="AKIAIOSFODNN7EXAMPLE",
            container_uid=1000,
            container_main_gid=1000,
            container_gids=[1000, 1001],
            group_ids=["group-1", "group-2"],
        )

        adapter = UserAdapter()
        updater = adapter.build_updater(request, email="old@example.com")
        spec = cast(UserUpdaterSpec, updater.spec)

        assert spec.username.value() == "newuser"
        assert spec.need_password_change.value() is True
        assert spec.full_name.value() == "New User"
        assert spec.description.value() == "A new user"
        assert spec.status.value() == UserStatus.ACTIVE
        assert spec.role.value() == DataUserRole.ADMIN
        assert spec.domain_name.value() == "new-domain"
        assert spec.allowed_client_ip.value() == ["192.168.1.1"]
        assert spec.totp_activated.value() is True
        assert spec.resource_policy.value() == "default"
        assert spec.sudo_session_enabled.value() is True
        assert spec.main_access_key.value() == "AKIAIOSFODNN7EXAMPLE"
        assert spec.container_uid.value() == 1000
        assert spec.container_main_gid.value() == 1000
        assert spec.container_gids.value() == [1000, 1001]
        assert spec.group_ids.value() == ["group-1", "group-2"]
        # pk_value is dummy UUID(int=0) since email-based lookup is used
        assert updater.pk_value == UUID(int=0)

    def test_build_updater_partial_fields(self) -> None:
        """Test building updater with only some fields set"""
        request = UpdateUserRequest(
            username="updated-name",
            status=UserStatusDTO.INACTIVE,
        )

        adapter = UserAdapter()
        updater = adapter.build_updater(request, email="user@example.com")
        spec = cast(UserUpdaterSpec, updater.spec)

        assert spec.username.value() == "updated-name"
        assert spec.status.value() == UserStatus.INACTIVE
        # Unset fields should be nop
        assert spec.password.optional_value() is None
        assert spec.need_password_change.optional_value() is None
        assert spec.full_name.optional_value() is None
        assert spec.description.optional_value() is None
        assert spec.role.optional_value() is None
        assert spec.domain_name.optional_value() is None
        assert spec.allowed_client_ip.optional_value() is None
        assert spec.totp_activated.optional_value() is None
        assert spec.resource_policy.optional_value() is None
        assert spec.sudo_session_enabled.optional_value() is None
        assert spec.main_access_key.optional_value() is None
        assert spec.container_uid.optional_value() is None
        assert spec.container_main_gid.optional_value() is None
        assert spec.container_gids.optional_value() is None
        assert spec.group_ids.optional_value() is None

    def test_build_updater_with_password(self) -> None:
        """Test building updater with password info"""
        request = UpdateUserRequest(
            username="updated-name",
        )
        password_info = PasswordInfo(
            password="newpassword123",
            algorithm=PasswordHashAlgorithm.SHA256,
            rounds=100000,
            salt_size=16,
        )

        adapter = UserAdapter()
        updater = adapter.build_updater(
            request, email="user@example.com", password_info=password_info
        )
        spec = cast(UserUpdaterSpec, updater.spec)

        assert spec.username.value() == "updated-name"
        assert spec.password.value() == password_info


class TestUserAdapterConversion:
    """Test cases for UserAdapter.convert_to_dto"""

    def test_convert_to_dto(self) -> None:
        """Test converting UserData to UserDTO with all fields"""
        now = datetime.now(tz=UTC)
        user_id = uuid4()

        user_data = UserData(
            id=user_id,
            uuid=user_id,
            username="testuser",
            email="test@example.com",
            need_password_change=False,
            full_name="Test User",
            description="A test user",
            is_active=True,
            status="active",
            status_info="OK",
            created_at=now,
            modified_at=now,
            domain_name="default",
            role=DataUserRole.USER,
            resource_policy="default",
            allowed_client_ip=["10.0.0.1"],
            totp_activated=True,
            totp_activated_at=now,
            sudo_session_enabled=False,
            main_access_key="AKIAIOSFODNN7EXAMPLE",
            container_uid=1000,
            container_main_gid=1000,
            container_gids=[1000, 1001],
        )

        adapter = UserAdapter()
        dto = adapter.convert_to_dto(user_data)

        assert isinstance(dto, UserDTO)
        assert dto.id == user_id
        assert dto.username == "testuser"
        assert dto.email == "test@example.com"
        assert dto.need_password_change is False
        assert dto.full_name == "Test User"
        assert dto.description == "A test user"
        assert dto.status == UserStatusDTO.ACTIVE
        assert dto.status_info == "OK"
        assert dto.created_at == now
        assert dto.modified_at == now
        assert dto.domain_name == "default"
        assert dto.role == UserRoleDTO.USER
        assert dto.resource_policy == "default"
        assert dto.allowed_client_ip == ["10.0.0.1"]
        assert dto.totp_activated is True
        assert dto.sudo_session_enabled is False
        assert dto.main_access_key == "AKIAIOSFODNN7EXAMPLE"
        assert dto.container_uid == 1000
        assert dto.container_main_gid == 1000
        assert dto.container_gids == [1000, 1001]

    def test_convert_to_dto_with_nulls(self) -> None:
        """Test converting UserData with optional fields as None"""
        user_id = uuid4()

        user_data = UserData(
            id=user_id,
            uuid=user_id,
            username=None,
            email="minimal@example.com",
            need_password_change=None,
            full_name=None,
            description=None,
            is_active=True,
            status="active",
            status_info=None,
            created_at=None,
            modified_at=None,
            domain_name=None,
            role=None,
            resource_policy="default",
            allowed_client_ip=None,
            totp_activated=None,
            totp_activated_at=None,
            sudo_session_enabled=False,
            main_access_key=None,
            container_uid=None,
            container_main_gid=None,
            container_gids=None,
        )

        adapter = UserAdapter()
        dto = adapter.convert_to_dto(user_data)

        assert isinstance(dto, UserDTO)
        assert dto.id == user_id
        assert dto.username is None
        assert dto.email == "minimal@example.com"
        assert dto.need_password_change is None
        assert dto.full_name is None
        assert dto.description is None
        assert dto.status == UserStatusDTO.ACTIVE
        assert dto.status_info is None
        assert dto.created_at is None
        assert dto.modified_at is None
        assert dto.domain_name is None
        assert dto.role is None
        assert dto.resource_policy == "default"
        assert dto.allowed_client_ip is None
        assert dto.totp_activated is None
        assert dto.sudo_session_enabled is False
        assert dto.main_access_key is None
        assert dto.container_uid is None
        assert dto.container_main_gid is None
        assert dto.container_gids is None
