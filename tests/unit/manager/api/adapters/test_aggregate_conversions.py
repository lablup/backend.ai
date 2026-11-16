"""The aggregate conversions of BaseAdapter: group inputs, orders and result values."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.dto.manager.v2.aggregate.request import (
    DateTimeGroup,
    EnumGroup,
    StringGroup,
    UUIDGroup,
)
from ai.backend.common.dto.manager.v2.aggregate.response import (
    AggregateValueInfo,
    DateTimeBucketInfo,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.specs.aggregate.aggregator import (
    AggregateValue,
    CountOrder,
    GroupKeyOrder,
)
from ai.backend.manager.models.specs.aggregate.group import (
    DateTimeBucket,
    DateTimeGroupBy,
    DateTimeGroupField,
    EnumGroupField,
    StringGroupField,
    UUIDGroupField,
)
from ai.backend.manager.models.specs.search.field import SearchableField


class _Status(enum.StrEnum):
    OK = "ok"
    FAILED = "failed"


class _ItemRow(Base):
    __tablename__ = "test_aggregate_conversion_items"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column("id", GUID(), primary_key=True)
    status: Mapped[_Status] = mapped_column("status", StrEnumType(_Status), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column("owner_id", GUID(), nullable=True)
    label: Mapped[str | None] = mapped_column("label", sa.String(64), nullable=True)


class _ItemAggregateFields:
    status = EnumGroupField(SearchableField(_ItemRow.status, None, None), _Status)
    created_at = DateTimeGroupField(SearchableField(_ItemRow.created_at, None, None))
    owner_id = UUIDGroupField(SearchableField(_ItemRow.owner_id, None, None))
    label = StringGroupField(SearchableField(_ItemRow.label, None, None))


@pytest.fixture
def adapter() -> BaseAdapter:
    return BaseAdapter()


class TestGroupConversion:
    def test_an_absent_group_asks_for_nothing(self, adapter: BaseAdapter) -> None:
        fields = _ItemAggregateFields

        assert adapter.apply_enum_group(None, fields.status) == []
        assert adapter.apply_datetime_group(None, fields.created_at) == []
        assert adapter.apply_uuid_group(None, fields.owner_id) == []
        assert adapter.apply_string_group(None, fields.label) == []

    @pytest.mark.parametrize(
        ("include_empty", "empty_values"),
        [(True, [_Status.OK, _Status.FAILED]), (False, [])],
    )
    def test_enum_group_fills_the_values_no_row_has_only_when_asked(
        self, adapter: BaseAdapter, include_empty: bool, empty_values: list[_Status]
    ) -> None:
        groups = adapter.apply_enum_group(
            EnumGroup(include_empty=include_empty), _ItemAggregateFields.status
        )

        assert len(groups) == 1
        assert list(groups[0].empty_values()) == empty_values

    @pytest.mark.parametrize(
        ("timezone", "expected"),
        [("Asia/Seoul", ZoneInfo("Asia/Seoul")), (None, ZoneInfo("UTC"))],
    )
    def test_datetime_group_takes_the_interval_and_the_time_zone(
        self, adapter: BaseAdapter, timezone: str | None, expected: ZoneInfo
    ) -> None:
        groups = adapter.apply_datetime_group(
            DateTimeGroup(interval_seconds=3600, timezone=timezone),
            _ItemAggregateFields.created_at,
        )

        assert len(groups) == 1
        group = groups[0]
        assert isinstance(group, DateTimeGroupBy)
        assert group.interval == timedelta(hours=1)
        assert group.timezone == expected

    @pytest.mark.parametrize("include_null", [True, False])
    def test_uuid_and_string_groups_keep_the_null_choice(
        self, adapter: BaseAdapter, include_null: bool
    ) -> None:
        uuid_groups = adapter.apply_uuid_group(
            UUIDGroup(include_null=include_null), _ItemAggregateFields.owner_id
        )
        string_groups = adapter.apply_string_group(
            StringGroup(include_null=include_null), _ItemAggregateFields.label
        )

        assert [group.include_null() for group in uuid_groups] == [include_null]
        assert [group.include_null() for group in string_groups] == [include_null]


class TestOrderConversion:
    @pytest.mark.parametrize(
        ("direction", "ascending"),
        [(OrderDirection.ASC, True), (OrderDirection.DESC, False)],
    )
    def test_key_order_orders_by_the_group_of_the_field(
        self, adapter: BaseAdapter, direction: OrderDirection, ascending: bool
    ) -> None:
        groups = adapter.apply_string_group(StringGroup(), _ItemAggregateFields.label)

        order = adapter.key_order(direction, groups, "label")

        assert order == GroupKeyOrder(groups[0], ascending=ascending)

    def test_key_order_of_a_field_not_in_group_by_is_refused(self, adapter: BaseAdapter) -> None:
        with pytest.raises(InvalidAPIParameters):
            adapter.key_order(OrderDirection.ASC, [], "label")

    @pytest.mark.parametrize(
        ("direction", "ascending"),
        [(OrderDirection.ASC, True), (OrderDirection.DESC, False)],
    )
    def test_count_order_follows_the_direction(
        self, adapter: BaseAdapter, direction: OrderDirection, ascending: bool
    ) -> None:
        assert adapter.count_order(direction) == CountOrder(ascending=ascending)


class TestResultConversion:
    def test_aggregate_value_carries_the_count(self, adapter: BaseAdapter) -> None:
        assert adapter.aggregate_value_info(AggregateValue(count=3)) == AggregateValueInfo(count=3)

    def test_datetime_bucket_carries_the_half_open_range(self, adapter: BaseAdapter) -> None:
        start = datetime(2026, 1, 5, tzinfo=UTC)
        end = start + timedelta(hours=1)

        info = adapter.datetime_bucket_info(DateTimeBucket(start=start, end=end))

        assert info == DateTimeBucketInfo(start=start, end=end)

    def test_a_null_bucket_stays_null(self, adapter: BaseAdapter) -> None:
        assert adapter.datetime_bucket_info(None) is None
