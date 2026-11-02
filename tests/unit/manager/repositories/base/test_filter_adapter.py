from __future__ import annotations

import enum
import uuid
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
import sqlalchemy as sa

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.filter_specs import (
    StringInMatchSpec,
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.common.dto.manager.query import (
    ArrayFilter,
    DateTimeFilter,
    EnumFilter,
    IntFilter,
    StringFilter,
    ToManyFilter,
    UUIDFilter,
)
from ai.backend.manager.errors.repository import EmptyMatchConditionError
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.array import ArrayConditions
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
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
    def equals(self, value: datetime) -> QueryCondition:
        return Recorded("equals", value)

    @override
    def before(self, value: datetime) -> QueryCondition:
        return Recorded("before", value)

    @override
    def after(self, value: datetime) -> QueryCondition:
        return Recorded("after", value)


class RecordingIntConditions(IntConditions):
    @override
    def equals(self, value: int) -> QueryCondition:
        return Recorded("equals", value)

    @override
    def not_equals(self, value: int) -> QueryCondition:
        return Recorded("not_equals", value)

    @override
    def greater_than(self, value: int) -> QueryCondition:
        return Recorded("greater_than", value)

    @override
    def greater_than_or_equal(self, value: int) -> QueryCondition:
        return Recorded("greater_than_or_equal", value)

    @override
    def less_than(self, value: int) -> QueryCondition:
        return Recorded("less_than", value)

    @override
    def less_than_or_equal(self, value: int) -> QueryCondition:
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
    def equals(self, value: ColumnStatus) -> QueryCondition:
        return Recorded("equals", value)

    @override
    def not_equals(self, value: ColumnStatus) -> QueryCondition:
        return Recorded("not_equals", value)

    @override
    def in_(self, values: Collection[ColumnStatus]) -> QueryCondition:
        return Recorded("in_", list(values))

    @override
    def not_in(self, values: Collection[ColumnStatus]) -> QueryCondition:
        return Recorded("not_in", list(values))


class RecordingBoolConditions(BoolConditions):
    @override
    def equals(self, value: bool) -> QueryCondition:
        return Recorded("equals", value)


class RecordingArrayConditions(ArrayConditions[int]):
    @override
    def contains(self, value: int) -> QueryCondition:
        return Recorded("contains", value)

    @override
    def contains_all(self, values: Sequence[int]) -> QueryCondition:
        return Recorded("contains_all", list(values))

    @override
    def contains_any(self, values: Sequence[int]) -> QueryCondition:
        return Recorded("contains_any", list(values))


class RecordingToManyCorrelation(ToManyCorrelation):
    @override
    def exists(self) -> QueryCondition:
        return Recorded("exists", [])

    @override
    def not_exists(self) -> QueryCondition:
        return Recorded("not_exists", [])

    @override
    def some(self, conditions: list[QueryCondition]) -> QueryCondition:
        return Recorded("some", conditions)

    @override
    def every(self, conditions: list[QueryCondition]) -> QueryCondition:
        return Recorded("every", conditions)

    @override
    def none(self, conditions: list[QueryCondition]) -> QueryCondition:
        return Recorded("none", conditions)


class RowFilter(BaseRequestModel):
    key: str | None = None


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


class TestApplyArrayFilter:
    @pytest.fixture
    def conditions(self, column: sa.sql.expression.ColumnClause[Any]) -> RecordingArrayConditions:
        return RecordingArrayConditions(column, sa.Integer())

    @pytest.mark.parametrize(
        ("filter_input", "expected"),
        [
            ({"contains": 1000}, Recorded("contains", 1000)),
            ({"contains_any": [1000, 1001]}, Recorded("contains_any", [1000, 1001])),
            ({"contains_all": [1000, 1001]}, Recorded("contains_all", [1000, 1001])),
        ],
    )
    def test_each_field_calls_its_operation(
        self,
        adapter: BaseFilterAdapter,
        conditions: RecordingArrayConditions,
        filter_input: dict[str, Any],
        expected: Recorded,
    ) -> None:
        applied = adapter.apply_array_filter(
            ArrayFilter[int].model_validate(filter_input), conditions
        )

        assert applied == [expected]

    def test_every_set_field_applies_in_order(
        self, adapter: BaseFilterAdapter, conditions: RecordingArrayConditions
    ) -> None:
        applied = adapter.apply_array_filter(
            ArrayFilter[int](contains_all=[1002], contains_any=[1001], contains=1000),
            conditions,
        )

        assert applied == [
            Recorded("contains", 1000),
            Recorded("contains_any", [1001]),
            Recorded("contains_all", [1002]),
        ]

    def test_zero_is_a_set_value(
        self, adapter: BaseFilterAdapter, conditions: RecordingArrayConditions
    ) -> None:
        applied = adapter.apply_array_filter(ArrayFilter[int](contains=0), conditions)

        assert applied == [Recorded("contains", 0)]

    def test_none_applies_nothing(
        self, adapter: BaseFilterAdapter, conditions: RecordingArrayConditions
    ) -> None:
        assert adapter.apply_array_filter(None, conditions) == []

    def test_empty_filter_applies_nothing(
        self, adapter: BaseFilterAdapter, conditions: RecordingArrayConditions
    ) -> None:
        assert adapter.apply_array_filter(ArrayFilter[int](), conditions) == []


class TestApplyToManyFilter:
    @pytest.fixture
    def correlation(
        self, column: sa.sql.expression.ColumnClause[Any]
    ) -> RecordingToManyCorrelation:
        return RecordingToManyCorrelation(sa.table("rows"), sa.table("owners"), column == column)

    @pytest.fixture
    def row_conditions(self) -> Callable[[RowFilter], list[QueryCondition]]:
        def convert(row_filter: RowFilter) -> list[QueryCondition]:
            return [Recorded("row", row_filter.key)]

        return convert

    @pytest.mark.parametrize("quantifier", ["some", "every", "none"])
    def test_each_quantifier_wraps_the_row_conditions(
        self,
        adapter: BaseFilterAdapter,
        correlation: RecordingToManyCorrelation,
        row_conditions: Callable[[RowFilter], list[QueryCondition]],
        quantifier: str,
    ) -> None:
        applied = adapter.apply_to_many_filter(
            ToManyFilter[RowFilter].model_validate({quantifier: {"key": "a"}}),
            correlation,
            row_conditions,
        )

        assert applied == [Recorded(quantifier, [Recorded("row", "a")])]

    @pytest.mark.parametrize(("asked", "expected"), [(True, "exists"), (False, "not_exists")])
    def test_exists_asks_only_whether_a_related_row_is_there(
        self,
        adapter: BaseFilterAdapter,
        correlation: RecordingToManyCorrelation,
        row_conditions: Callable[[RowFilter], list[QueryCondition]],
        asked: bool,
        expected: str,
    ) -> None:
        applied = adapter.apply_to_many_filter(
            ToManyFilter[RowFilter](exists=asked), correlation, row_conditions
        )

        assert applied == [Recorded(expected, [])]

    @pytest.mark.parametrize("quantifier", ["some", "every", "none"])
    def test_a_quantifier_with_no_condition_is_refused(
        self,
        adapter: BaseFilterAdapter,
        quantifier: str,
    ) -> None:
        """A row filter with nothing set reduces to no condition, which `exists` says."""

        def no_conditions(_row_filter: RowFilter) -> list[QueryCondition]:
            return []

        with pytest.raises(EmptyMatchConditionError):
            adapter.apply_to_many_filter(
                ToManyFilter[RowFilter].model_validate({quantifier: {}}),
                ToManyCorrelation(sa.table("rows"), sa.table("owners"), sa.true()),
                no_conditions,
            )

    def test_every_set_quantifier_applies_in_order(
        self,
        adapter: BaseFilterAdapter,
        correlation: RecordingToManyCorrelation,
        row_conditions: Callable[[RowFilter], list[QueryCondition]],
    ) -> None:
        applied = adapter.apply_to_many_filter(
            ToManyFilter[RowFilter](
                none=RowFilter(key="c"), every=RowFilter(key="b"), some=RowFilter(key="a")
            ),
            correlation,
            row_conditions,
        )

        assert applied == [
            Recorded("some", [Recorded("row", "a")]),
            Recorded("every", [Recorded("row", "b")]),
            Recorded("none", [Recorded("row", "c")]),
        ]

    def test_none_applies_nothing(
        self,
        adapter: BaseFilterAdapter,
        correlation: RecordingToManyCorrelation,
        row_conditions: Callable[[RowFilter], list[QueryCondition]],
    ) -> None:
        assert adapter.apply_to_many_filter(None, correlation, row_conditions) == []
