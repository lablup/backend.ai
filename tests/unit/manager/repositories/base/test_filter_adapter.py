from __future__ import annotations

import enum
import uuid
from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringInMatchSpec,
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    EnumFilter,
    IntFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

FIRST_ID = uuid.UUID(int=1)
SECOND_ID = uuid.UUID(int=2)
EARLIER = datetime(2026, 1, 1, tzinfo=UTC)
LATER = datetime(2026, 2, 1, tzinfo=UTC)


@dataclass(frozen=True)
class Recorded:
    """The operation a conditions object was asked for, and with what."""

    operation: str
    argument: object

    def __call__(self) -> sa.sql.expression.ColumnElement[bool]:
        return sa.true()


class RecordingStringConditions(StringConditions):
    @override
    def contains(self, spec: StringMatchSpec) -> QueryCondition:
        return Recorded("contains", spec)

    @override
    def starts_with(self, spec: StringMatchSpec) -> QueryCondition:
        return Recorded("starts_with", spec)

    @override
    def ends_with(self, spec: StringMatchSpec) -> QueryCondition:
        return Recorded("ends_with", spec)

    @override
    def equals(self, spec: StringMatchSpec) -> QueryCondition:
        return Recorded("equals", spec)

    @override
    def in_(self, spec: StringInMatchSpec) -> QueryCondition:
        return Recorded("in_", spec)


class RecordingUUIDConditions(UUIDConditions):
    @override
    def equals(self, spec: UUIDEqualMatchSpec) -> QueryCondition:
        return Recorded("equals", spec)

    @override
    def in_(self, spec: UUIDInMatchSpec) -> QueryCondition:
        return Recorded("in_", spec)


class RecordingDateTimeConditions(DateTimeConditions):
    @override
    def equals(self, value: datetime | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("equals", value)

    @override
    def before(self, value: datetime | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("before", value)

    @override
    def after(self, value: datetime | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("after", value)


class RecordingIntConditions(IntConditions):
    @override
    def equals(self, value: int | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("equals", value)

    @override
    def not_equals(self, value: int | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("not_equals", value)

    @override
    def greater_than(self, value: int | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("greater_than", value)

    @override
    def greater_than_or_equal(self, value: int | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("greater_than_or_equal", value)

    @override
    def less_than(self, value: int | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("less_than", value)

    @override
    def less_than_or_equal(self, value: int | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("less_than_or_equal", value)


class ColumnStatus(enum.Enum):
    ACTIVE = "active"
    DELETED = "deleted"


class RequestStatus(enum.StrEnum):
    ACTIVE = "active"
    DELETED = "deleted"


class RequestStatusFilter(EnumFilter[RequestStatus]):
    pass


class RecordingEnumConditions(EnumConditions[ColumnStatus]):
    @override
    def equals(self, value: ColumnStatus | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("equals", value)

    @override
    def not_equals(self, value: ColumnStatus | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("not_equals", value)

    @override
    def in_(self, values: Collection[ColumnStatus] | None) -> QueryCondition | None:
        if values is None:
            return None
        return Recorded("in_", list(values))

    @override
    def not_in(self, values: Collection[ColumnStatus] | None) -> QueryCondition | None:
        if values is None:
            return None
        return Recorded("not_in", list(values))


class RecordingBoolConditions(BoolConditions):
    @override
    def equals(self, value: bool | None) -> QueryCondition | None:
        if value is None:
            return None
        return Recorded("equals", value)


@pytest.fixture
def adapter() -> BaseFilterAdapter:
    return BaseFilterAdapter()


@pytest.fixture
def column() -> sa.sql.expression.ColumnClause[Any]:
    return sa.column("target")


class TestApplyStringFilter:
    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"equals": "v"}, Recorded("equals", StringMatchSpec("v", False, False))),
            ({"i_equals": "v"}, Recorded("equals", StringMatchSpec("v", True, False))),
            ({"not_equals": "v"}, Recorded("equals", StringMatchSpec("v", False, True))),
            ({"i_not_equals": "v"}, Recorded("equals", StringMatchSpec("v", True, True))),
            ({"contains": "v"}, Recorded("contains", StringMatchSpec("v", False, False))),
            ({"i_contains": "v"}, Recorded("contains", StringMatchSpec("v", True, False))),
            ({"not_contains": "v"}, Recorded("contains", StringMatchSpec("v", False, True))),
            ({"i_not_contains": "v"}, Recorded("contains", StringMatchSpec("v", True, True))),
            ({"starts_with": "v"}, Recorded("starts_with", StringMatchSpec("v", False, False))),
            ({"i_starts_with": "v"}, Recorded("starts_with", StringMatchSpec("v", True, False))),
            (
                {"not_starts_with": "v"},
                Recorded("starts_with", StringMatchSpec("v", False, True)),
            ),
            (
                {"i_not_starts_with": "v"},
                Recorded("starts_with", StringMatchSpec("v", True, True)),
            ),
            ({"ends_with": "v"}, Recorded("ends_with", StringMatchSpec("v", False, False))),
            ({"i_ends_with": "v"}, Recorded("ends_with", StringMatchSpec("v", True, False))),
            ({"not_ends_with": "v"}, Recorded("ends_with", StringMatchSpec("v", False, True))),
            ({"i_not_ends_with": "v"}, Recorded("ends_with", StringMatchSpec("v", True, True))),
            ({"in": ["v"]}, Recorded("in_", StringInMatchSpec(["v"], False, False))),
            ({"not_in": ["v"]}, Recorded("in_", StringInMatchSpec(["v"], False, True))),
            ({"i_in": ["v"]}, Recorded("in_", StringInMatchSpec(["v"], True, False))),
            ({"i_not_in": ["v"]}, Recorded("in_", StringInMatchSpec(["v"], True, True))),
        ],
    )
    def test_each_field_calls_its_operation(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_string_filter(
            StringFilter.model_validate(filter_input), RecordingStringConditions(column)
        )

        assert applied == [expected]

    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            (
                {"i_equals": "a", "equals": "b"},
                Recorded("equals", StringMatchSpec("b", False, False)),
            ),
            (
                {"contains": "a", "i_not_equals": "b"},
                Recorded("equals", StringMatchSpec("b", True, True)),
            ),
            (
                {"in": ["a"], "i_not_ends_with": "b"},
                Recorded("ends_with", StringMatchSpec("b", True, True)),
            ),
            (
                {"i_in": ["a"], "not_in": ["b"]},
                Recorded("in_", StringInMatchSpec(["b"], False, True)),
            ),
        ],
    )
    def test_only_the_first_set_field_applies(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_string_filter(
            StringFilter.model_validate(filter_input), RecordingStringConditions(column)
        )

        assert applied == [expected]

    def test_empty_string_is_a_set_value(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        applied = adapter.apply_string_filter(
            StringFilter(equals=""), RecordingStringConditions(column)
        )

        assert applied == [Recorded("equals", StringMatchSpec("", False, False))]

    def test_none_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_string_filter(None, RecordingStringConditions(column)) == []

    def test_empty_filter_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_string_filter(StringFilter(), RecordingStringConditions(column)) == []


class TestApplyUUIDFilter:
    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"equals": FIRST_ID}, Recorded("equals", UUIDEqualMatchSpec(FIRST_ID, False))),
            ({"not_equals": FIRST_ID}, Recorded("equals", UUIDEqualMatchSpec(FIRST_ID, True))),
            ({"in": [FIRST_ID]}, Recorded("in_", UUIDInMatchSpec([FIRST_ID], False))),
            ({"not_in": [FIRST_ID]}, Recorded("in_", UUIDInMatchSpec([FIRST_ID], True))),
        ],
    )
    def test_each_field_calls_its_operation(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_uuid_filter(
            UUIDFilter.model_validate(filter_input), RecordingUUIDConditions(column)
        )

        assert applied == [expected]

    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            (
                {"not_equals": SECOND_ID, "equals": FIRST_ID},
                Recorded("equals", UUIDEqualMatchSpec(FIRST_ID, False)),
            ),
            (
                {"in": [SECOND_ID], "not_equals": FIRST_ID},
                Recorded("equals", UUIDEqualMatchSpec(FIRST_ID, True)),
            ),
            (
                {"not_in": [SECOND_ID], "in": [FIRST_ID]},
                Recorded("in_", UUIDInMatchSpec([FIRST_ID], False)),
            ),
        ],
    )
    def test_only_the_first_set_field_applies(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_uuid_filter(
            UUIDFilter.model_validate(filter_input), RecordingUUIDConditions(column)
        )

        assert applied == [expected]

    def test_none_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_uuid_filter(None, RecordingUUIDConditions(column)) == []

    def test_empty_filter_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_uuid_filter(UUIDFilter(), RecordingUUIDConditions(column)) == []


class TestApplyDateTimeFilter:
    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"equals": EARLIER}, Recorded("equals", EARLIER)),
            ({"before": EARLIER}, Recorded("before", EARLIER)),
            ({"after": EARLIER}, Recorded("after", EARLIER)),
        ],
    )
    def test_each_field_calls_its_operation(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_datetime_filter(
            DateTimeFilter.model_validate(filter_input), RecordingDateTimeConditions(column)
        )

        assert applied == [expected]

    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"before": LATER, "equals": EARLIER}, Recorded("equals", EARLIER)),
            ({"after": LATER, "before": EARLIER}, Recorded("before", EARLIER)),
        ],
    )
    def test_only_the_first_set_field_applies(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_datetime_filter(
            DateTimeFilter.model_validate(filter_input), RecordingDateTimeConditions(column)
        )

        assert applied == [expected]

    def test_not_equals_is_not_applied(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        applied = adapter.apply_datetime_filter(
            DateTimeFilter(not_equals=EARLIER), RecordingDateTimeConditions(column)
        )

        assert applied == []

    def test_none_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_datetime_filter(None, RecordingDateTimeConditions(column)) == []


class TestApplyIntFilter:
    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"equals": 3}, Recorded("equals", 3)),
            ({"not_equals": 3}, Recorded("not_equals", 3)),
            ({"greater_than": 3}, Recorded("greater_than", 3)),
            ({"greater_than_or_equal": 3}, Recorded("greater_than_or_equal", 3)),
            ({"less_than": 3}, Recorded("less_than", 3)),
            ({"less_than_or_equal": 3}, Recorded("less_than_or_equal", 3)),
        ],
    )
    def test_each_field_calls_its_operation(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_int_filter(
            IntFilter.model_validate(filter_input), RecordingIntConditions(column)
        )

        assert applied == [expected]

    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"not_equals": 1, "equals": 2}, Recorded("equals", 2)),
            ({"less_than": 1, "greater_than": 2}, Recorded("greater_than", 2)),
            ({"less_than_or_equal": 1, "less_than": 2}, Recorded("less_than", 2)),
        ],
    )
    def test_only_the_first_set_field_applies(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_int_filter(
            IntFilter.model_validate(filter_input), RecordingIntConditions(column)
        )

        assert applied == [expected]

    def test_zero_is_a_set_value(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        applied = adapter.apply_int_filter(IntFilter(equals=0), RecordingIntConditions(column))

        assert applied == [Recorded("equals", 0)]

    def test_none_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_int_filter(None, RecordingIntConditions(column)) == []

    def test_empty_filter_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_int_filter(IntFilter(), RecordingIntConditions(column)) == []


class TestApplyEnumFilter:
    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"equals": "active"}, Recorded("equals", ColumnStatus.ACTIVE)),
            ({"in": ["active", "deleted"]}, Recorded("in_", list(ColumnStatus))),
            ({"not_equals": "active"}, Recorded("not_equals", ColumnStatus.ACTIVE)),
            ({"not_in": ["deleted"]}, Recorded("not_in", [ColumnStatus.DELETED])),
        ],
    )
    def test_each_field_calls_its_operation_with_column_values(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_enum_filter(
            RequestStatusFilter.model_validate(filter_input),
            RecordingEnumConditions(column, ColumnStatus),
        )

        assert applied == [expected]

    def test_every_set_field_applies_in_order(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        applied = adapter.apply_enum_filter(
            RequestStatusFilter(
                not_in=[RequestStatus.DELETED],
                not_equals=RequestStatus.DELETED,
                in_=[RequestStatus.ACTIVE],
                equals=RequestStatus.ACTIVE,
            ),
            RecordingEnumConditions(column, ColumnStatus),
        )

        assert applied == [
            Recorded("equals", ColumnStatus.ACTIVE),
            Recorded("in_", [ColumnStatus.ACTIVE]),
            Recorded("not_equals", ColumnStatus.DELETED),
            Recorded("not_in", [ColumnStatus.DELETED]),
        ]

    def test_none_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        applied = adapter.apply_enum_filter(None, RecordingEnumConditions(column, ColumnStatus))

        assert applied == []

    def test_empty_filter_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        applied = adapter.apply_enum_filter(
            RequestStatusFilter(), RecordingEnumConditions(column, ColumnStatus)
        )

        assert applied == []


class TestApplyBoolFilter:
    @pytest.mark.parametrize("value", [True, False])
    def test_value_calls_equals(
        self,
        adapter: BaseFilterAdapter,
        column: sa.sql.expression.ColumnClause[Any],
        value: bool,
    ) -> None:
        applied = adapter.apply_bool_filter(value, RecordingBoolConditions(column))

        assert applied == [Recorded("equals", value)]

    def test_none_applies_nothing(
        self, adapter: BaseFilterAdapter, column: sa.sql.expression.ColumnClause[Any]
    ) -> None:
        assert adapter.apply_bool_filter(None, RecordingBoolConditions(column)) == []
