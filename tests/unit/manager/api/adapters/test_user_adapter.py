"""Tests for v2 UserAdapter conversion and its DataLoader path."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole as DataUserRole
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    NullableDateTimeFilter,
    UUIDFilter,
)
from ai.backend.common.dto.manager.v2.keypair.request import KeypairFilter
from ai.backend.common.dto.manager.v2.user.request import (
    KeypairNestedFilter,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.types import OrderDirection, UserOrderField
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.common import GenericForbidden


def _create_user_data(
    user_id: UUID | None = None,
) -> UserData:
    """Create a minimal UserData for testing adapter conversion."""
    now = datetime.now(tz=UTC)
    effective_id = user_id or uuid4()
    return UserData(
        id=effective_id,
        uuid=effective_id,
        username="testuser",
        email="test@example.com",
        need_password_change=False,
        full_name="Test User",
        description="A test user",
        is_active=True,
        status="active",
        status_info=None,
        created_at=now,
        modified_at=now,
        domain_name="default",
        domain_id=DomainID(uuid4()),
        role=DataUserRole.USER,
        resource_policy="default",
        allowed_client_ip=None,
        totp_activated=False,
        totp_activated_at=None,
        sudo_session_enabled=False,
        container_uid=None,
        container_main_gid=None,
        container_gids=None,
        integration_name="ext-test-system",
    )


class TestUserDataToNode:
    """Tests for _user_data_to_node conversion."""

    def test_basic_fields_mapped_correctly(self) -> None:
        """UserData fields should map to UserNode sub-models."""
        user_id = uuid4()
        data = _create_user_data(user_id=user_id)
        node = UserAdapter._user_data_to_node(data, None)

        assert node.id == user_id
        assert node.basic_info.username == "testuser"
        assert node.basic_info.email == "test@example.com"
        assert node.basic_info.full_name == "Test User"
        assert node.basic_info.description == "A test user"
        assert node.basic_info.integration_name == "ext-test-system"
        assert node.organization.domain_name == "default"
        assert node.organization.resource_policy == "default"
        assert node.status.need_password_change is False
        assert node.security.totp_activated is False
        assert node.container.container_uid is None

    def test_node_has_no_groups_field(self) -> None:
        """UserNode should not have a groups field."""
        data = _create_user_data()
        node = UserAdapter._user_data_to_node(data, None)
        assert not hasattr(node, "groups")


class TestBatchLoadByIds:
    @pytest.fixture
    def readable(self) -> UserData:
        return _create_user_data()

    @pytest.fixture
    def denial(self) -> GenericForbidden:
        return GenericForbidden("no read on this user")

    @pytest.fixture
    def processors(self, readable: UserData, denial: GenericForbidden) -> MagicMock:
        processors = MagicMock()
        processors.bulk_get.run = AsyncMock(
            return_value=PartialBulkResult(
                items=[
                    PartialBulkEntityResult[UserData].succeeded(UserID(readable.uuid), readable),
                    PartialBulkEntityResult[UserData].denied(UserID(uuid4()), denial),
                    PartialBulkEntityResult[UserData].nothing(UserID(uuid4())),
                ]
            )
        )
        processors.get_default_keypairs.run = AsyncMock(return_value=MagicMock(designated={}))
        return processors

    @pytest.fixture
    def adapter(self, processors: MagicMock) -> UserAdapter:
        return UserAdapter(processors, MagicMock(), MagicMock(), MagicMock())

    async def test_answers_per_id(
        self,
        adapter: UserAdapter,
        processors: MagicMock,
        readable: UserData,
        denial: GenericForbidden,
    ) -> None:
        ids = [UserID(readable.uuid), UserID(uuid4()), UserID(uuid4())]

        node, refused, missing = await adapter.batch_load_by_ids(ids)

        assert node is not None and not isinstance(node, Exception)
        assert node.id == readable.uuid
        assert refused is denial
        assert missing is None
        keypair_action = processors.get_default_keypairs.run.await_args.args[0]
        assert list(keypair_action.user_ids) == [UserID(readable.uuid)]

    async def test_no_ids_read_nothing(self, adapter: UserAdapter, processors: MagicMock) -> None:
        assert await adapter.batch_load_by_ids([]) == []
        processors.bulk_get.run.assert_not_awaited()


class TestUserOrderConversion:
    """Every order field the DTO publishes converts to a query order."""

    @pytest.fixture
    def adapter(self) -> UserAdapter:
        return UserAdapter(MagicMock(), MagicMock(), MagicMock(), MagicMock())

    @pytest.mark.parametrize("field", list(UserOrderField))
    def test_every_published_field_converts(
        self, adapter: UserAdapter, field: UserOrderField
    ) -> None:
        order = adapter._convert_user_order(UserOrder(field=field, direction=OrderDirection.ASC))

        assert order is not None

    @pytest.mark.parametrize("direction", list(OrderDirection))
    def test_direction_reaches_the_sql(
        self, adapter: UserAdapter, direction: OrderDirection
    ) -> None:
        order = adapter._convert_user_order(
            UserOrder(field=UserOrderField.TOTP_ACTIVATED_AT, direction=direction)
        )

        assert direction.value.upper() in str(order).upper()


class TestUserTimestampFilterConversion:
    """The timestamp filters opened alongside the declarations."""

    @pytest.fixture
    def adapter(self) -> UserAdapter:
        return UserAdapter(MagicMock(), MagicMock(), MagicMock(), MagicMock())

    def test_modified_at_reaches_the_updated_at_column(self, adapter: UserAdapter) -> None:
        conditions = adapter._convert_user_filter(
            UserFilter(modified_at=DateTimeFilter(after=datetime(2026, 1, 1, tzinfo=UTC)))
        )

        assert len(conditions) == 1
        assert "updated_at" in str(conditions[0]().compile())

    def test_totp_activated_at_asks_for_null(self, adapter: UserAdapter) -> None:
        conditions = adapter._convert_user_filter(
            UserFilter(totp_activated_at=NullableDateTimeFilter(is_null=True))
        )

        assert len(conditions) == 1
        assert "IS NULL" in str(conditions[0]().compile()).upper()

    def test_totp_activated_at_asks_for_not_null(self, adapter: UserAdapter) -> None:
        conditions = adapter._convert_user_filter(
            UserFilter(totp_activated_at=NullableDateTimeFilter(is_null=False))
        )

        assert len(conditions) == 1
        assert "IS NOT NULL" in str(conditions[0]().compile()).upper()

    def test_totp_activated_at_compares_when_no_null_check_is_asked(
        self, adapter: UserAdapter
    ) -> None:
        conditions = adapter._convert_user_filter(
            UserFilter(
                totp_activated_at=NullableDateTimeFilter(before=datetime(2026, 1, 1, tzinfo=UTC))
            )
        )

        assert len(conditions) == 1
        assert "totp_activated_at" in str(conditions[0]().compile())


class TestUserKeypairNestedFilterConversion:
    """A user search narrowed by conditions on the keypairs the user owns."""

    @pytest.fixture
    def adapter(self) -> UserAdapter:
        return UserAdapter(MagicMock(), MagicMock(), MagicMock(), MagicMock())

    def test_some_reaches_the_keypairs_table(self, adapter: UserAdapter) -> None:
        conditions = adapter._convert_user_filter(
            UserFilter(keypairs=KeypairNestedFilter(some=KeypairFilter(is_active=True)))
        )

        assert len(conditions) == 1
        sql = str(conditions[0]().compile())
        assert "EXISTS" in sql
        assert "keypairs" in sql

    def test_every_quantifier_negates_the_failing_row(self, adapter: UserAdapter) -> None:
        conditions = adapter._convert_user_filter(
            UserFilter(keypairs=KeypairNestedFilter(every=KeypairFilter(is_active=True)))
        )

        assert len(conditions) == 1
        assert "NOT (EXISTS" in str(conditions[0]().compile())

    def test_each_quantifier_applies_on_its_own(self, adapter: UserAdapter) -> None:
        conditions = adapter._convert_user_filter(
            UserFilter(
                keypairs=KeypairNestedFilter(
                    some=KeypairFilter(is_active=True),
                    none=KeypairFilter(is_admin=True),
                )
            )
        )

        assert len(conditions) == 2

    def test_domain_id_filters_the_domain_id_column(self, adapter: UserAdapter) -> None:
        conditions = adapter._convert_user_filter(UserFilter(domain_id=UUIDFilter(equals=uuid4())))

        assert len(conditions) == 1
        assert "domain_id" in str(conditions[0]().compile())
