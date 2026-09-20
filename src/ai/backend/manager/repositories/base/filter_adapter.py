"""
Base adapters for converting DTOs to repository query objects.
Provides reusable conversion logic for common patterns.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any, final

from ai.backend.common.data.filter_specs import (
    StringInMatchSpec,
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.common.dto.manager.query import (
    ArrayFilter,
    DateTimeFilter,
    DecimalFilter,
    EnumFilter,
    IntFilter,
    NullableDateTimeFilter,
    StringFilter,
    ToManyFilter,
    UUIDFilter,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import DecimalConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation


class BaseFilterAdapter:
    """Base adapter providing common filter conversion utilities."""

    @final
    def convert_string_filter(
        self,
        string_filter: StringFilter,
        contains_factory: Callable[[StringMatchSpec], QueryCondition],
        equals_factory: Callable[[StringMatchSpec], QueryCondition],
        starts_with_factory: Callable[[StringMatchSpec], QueryCondition],
        ends_with_factory: Callable[[StringMatchSpec], QueryCondition],
        in_factory: Callable[[StringInMatchSpec], QueryCondition],
    ) -> QueryCondition | None:
        """
        Convert StringFilter to QueryCondition using provided factory callables.

        The method signature matches GraphQL StringFilter.build_query_condition for consistency.

        Args:
            string_filter: The string filter to convert
            contains_factory: Factory for LIKE '%value%' operations
            equals_factory: Factory for exact match (=) operations
            starts_with_factory: Factory for LIKE 'value%' operations
            ends_with_factory: Factory for LIKE '%value' operations
            in_factory: Factory for IN (list membership) operations

        Returns:
            QueryCondition if any filter field is set, None otherwise
        """
        # equals operations
        if string_filter.equals is not None:
            return equals_factory(
                StringMatchSpec(string_filter.equals, case_insensitive=False, negated=False)
            )
        if string_filter.i_equals is not None:
            return equals_factory(
                StringMatchSpec(string_filter.i_equals, case_insensitive=True, negated=False)
            )
        if string_filter.not_equals is not None:
            return equals_factory(
                StringMatchSpec(string_filter.not_equals, case_insensitive=False, negated=True)
            )
        if string_filter.i_not_equals is not None:
            return equals_factory(
                StringMatchSpec(string_filter.i_not_equals, case_insensitive=True, negated=True)
            )

        # contains operations
        if string_filter.contains is not None:
            return contains_factory(
                StringMatchSpec(string_filter.contains, case_insensitive=False, negated=False)
            )
        if string_filter.i_contains is not None:
            return contains_factory(
                StringMatchSpec(string_filter.i_contains, case_insensitive=True, negated=False)
            )
        if string_filter.not_contains is not None:
            return contains_factory(
                StringMatchSpec(string_filter.not_contains, case_insensitive=False, negated=True)
            )
        if string_filter.i_not_contains is not None:
            return contains_factory(
                StringMatchSpec(string_filter.i_not_contains, case_insensitive=True, negated=True)
            )

        # starts_with operations
        if string_filter.starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(string_filter.starts_with, case_insensitive=False, negated=False)
            )
        if string_filter.i_starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(string_filter.i_starts_with, case_insensitive=True, negated=False)
            )
        if string_filter.not_starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(string_filter.not_starts_with, case_insensitive=False, negated=True)
            )
        if string_filter.i_not_starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(
                    string_filter.i_not_starts_with, case_insensitive=True, negated=True
                )
            )

        # ends_with operations
        if string_filter.ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(string_filter.ends_with, case_insensitive=False, negated=False)
            )
        if string_filter.i_ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(string_filter.i_ends_with, case_insensitive=True, negated=False)
            )
        if string_filter.not_ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(string_filter.not_ends_with, case_insensitive=False, negated=True)
            )
        if string_filter.i_not_ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(string_filter.i_not_ends_with, case_insensitive=True, negated=True)
            )

        # IN operations
        if string_filter.in_ is not None:
            return in_factory(
                StringInMatchSpec(values=string_filter.in_, case_insensitive=False, negated=False)
            )
        if string_filter.not_in is not None:
            return in_factory(
                StringInMatchSpec(values=string_filter.not_in, case_insensitive=False, negated=True)
            )
        if string_filter.i_in is not None:
            return in_factory(
                StringInMatchSpec(values=string_filter.i_in, case_insensitive=True, negated=False)
            )
        if string_filter.i_not_in is not None:
            return in_factory(
                StringInMatchSpec(
                    values=string_filter.i_not_in, case_insensitive=True, negated=True
                )
            )

        return None

    @final
    def convert_uuid_filter(
        self,
        uuid_filter: UUIDFilter,
        equals_factory: Callable[[UUIDEqualMatchSpec], QueryCondition],
        in_factory: Callable[[UUIDInMatchSpec], QueryCondition],
    ) -> QueryCondition | None:
        """
        Convert UUIDFilter to QueryCondition using provided factory callables.

        Args:
            uuid_filter: The UUID filter to convert
            equals_factory: Factory for equality operations (=, !=)
            in_factory: Factory for IN operations (IN, NOT IN)

        Returns:
            QueryCondition if any filter field is set, None otherwise
        """
        # Equality operations
        if uuid_filter.equals is not None:
            return equals_factory(UUIDEqualMatchSpec(value=uuid_filter.equals, negated=False))
        if uuid_filter.not_equals is not None:
            return equals_factory(UUIDEqualMatchSpec(value=uuid_filter.not_equals, negated=True))

        # IN operations
        if uuid_filter.in_ is not None:
            return in_factory(UUIDInMatchSpec(values=uuid_filter.in_, negated=False))
        if uuid_filter.not_in is not None:
            return in_factory(UUIDInMatchSpec(values=uuid_filter.not_in, negated=True))

        return None

    @final
    def convert_int_filter(
        self,
        int_filter: IntFilter,
        int_conditions: Any,
    ) -> QueryCondition | None:
        """Convert IntFilter to QueryCondition using a conditions class.

        The ``int_conditions`` object must have ``equals``, ``not_equals``,
        ``gt``, ``gte``, ``lt``, ``lte`` factory methods (as produced by
        ``_make_int_conditions`` in conditions modules).

        Args:
            int_filter: The integer filter to convert.
            int_conditions: Object with factory methods for each comparison.

        Returns:
            QueryCondition if any filter field is set, None otherwise.
        """
        return int_filter.build_query_condition(
            equals_factory=int_conditions.equals,
            not_equals_factory=int_conditions.not_equals,
            greater_than_factory=int_conditions.gt,
            greater_than_or_equal_factory=int_conditions.gte,
            less_than_factory=int_conditions.lt,
            less_than_or_equal_factory=int_conditions.lte,
        )

    @final
    def convert_array_filter(
        self,
        array_filter: ArrayFilter[Any],
        contains_factory: Callable[[Any], QueryCondition],
        contains_any_factory: Callable[[list[Any]], QueryCondition],
        contains_all_factory: Callable[[list[Any]], QueryCondition],
    ) -> QueryCondition | None:
        """Convert an ArrayFilter to a QueryCondition.

        Args:
            array_filter: The array filter to convert.
            contains_factory: Factory for "column contains this single value".
            contains_any_factory: Factory for "column contains ANY of these values".
            contains_all_factory: Factory for "column contains ALL of these values".

        Returns:
            QueryCondition if any filter field is set, None otherwise.
        """
        return array_filter.build_query_condition(
            contains_factory=contains_factory,
            contains_any_factory=contains_any_factory,
            contains_all_factory=contains_all_factory,
        )

    @final
    def apply_string_filter(
        self, string_filter: StringFilter | None, conditions: StringConditions
    ) -> list[QueryCondition]:
        """Apply the first operation ``string_filter`` sets."""
        if string_filter is None:
            return []
        match_operations: list[
            tuple[str | None, bool, bool, Callable[[StringMatchSpec], QueryCondition]]
        ] = [
            (string_filter.equals, False, False, conditions.equals),
            (string_filter.i_equals, True, False, conditions.equals),
            (string_filter.not_equals, False, True, conditions.equals),
            (string_filter.i_not_equals, True, True, conditions.equals),
            (string_filter.contains, False, False, conditions.contains),
            (string_filter.i_contains, True, False, conditions.contains),
            (string_filter.not_contains, False, True, conditions.contains),
            (string_filter.i_not_contains, True, True, conditions.contains),
            (string_filter.starts_with, False, False, conditions.starts_with),
            (string_filter.i_starts_with, True, False, conditions.starts_with),
            (string_filter.not_starts_with, False, True, conditions.starts_with),
            (string_filter.i_not_starts_with, True, True, conditions.starts_with),
            (string_filter.ends_with, False, False, conditions.ends_with),
            (string_filter.i_ends_with, True, False, conditions.ends_with),
            (string_filter.not_ends_with, False, True, conditions.ends_with),
            (string_filter.i_not_ends_with, True, True, conditions.ends_with),
        ]
        for value, case_insensitive, negated, operation in match_operations:
            if value is not None:
                return [
                    operation(
                        StringMatchSpec(value, case_insensitive=case_insensitive, negated=negated)
                    )
                ]
        in_operations: list[tuple[list[str] | None, bool, bool]] = [
            (string_filter.in_, False, False),
            (string_filter.not_in, False, True),
            (string_filter.i_in, True, False),
            (string_filter.i_not_in, True, True),
        ]
        for values, case_insensitive, negated in in_operations:
            if values is not None:
                return [
                    conditions.in_(
                        StringInMatchSpec(
                            values=values, case_insensitive=case_insensitive, negated=negated
                        )
                    )
                ]
        return []

    @final
    def apply_uuid_filter(
        self, uuid_filter: UUIDFilter | None, conditions: UUIDConditions
    ) -> list[QueryCondition]:
        """Apply the first operation ``uuid_filter`` sets."""
        if uuid_filter is None:
            return []
        if uuid_filter.equals is not None:
            return [conditions.equals(UUIDEqualMatchSpec(value=uuid_filter.equals, negated=False))]
        if uuid_filter.not_equals is not None:
            return [
                conditions.equals(UUIDEqualMatchSpec(value=uuid_filter.not_equals, negated=True))
            ]
        if uuid_filter.in_ is not None:
            return [conditions.in_(UUIDInMatchSpec(values=uuid_filter.in_, negated=False))]
        if uuid_filter.not_in is not None:
            return [conditions.in_(UUIDInMatchSpec(values=uuid_filter.not_in, negated=True))]
        return []

    @final
    def apply_datetime_filter(
        self, datetime_filter: DateTimeFilter | None, conditions: DateTimeConditions
    ) -> list[QueryCondition]:
        """Apply the first of ``equals``, ``before``, ``after``; ``not_equals`` is not applied."""
        if datetime_filter is None:
            return []
        if datetime_filter.equals is not None:
            return [conditions.equals(datetime_filter.equals)]
        if datetime_filter.before is not None:
            return [conditions.before(datetime_filter.before)]
        if datetime_filter.after is not None:
            return [conditions.after(datetime_filter.after)]
        return []

    @final
    def apply_nullable_datetime_filter(
        self, datetime_filter: NullableDateTimeFilter | None, conditions: DateTimeConditions
    ) -> list[QueryCondition]:
        """Apply ``is_null`` first, then what ``apply_datetime_filter`` applies."""
        if datetime_filter is None:
            return []
        if datetime_filter.is_null is not None:
            if datetime_filter.is_null:
                return [conditions.is_null()]
            return [conditions.is_not_null()]
        return self.apply_datetime_filter(datetime_filter, conditions)

    @final
    def apply_int_filter(
        self, int_filter: IntFilter | None, conditions: IntConditions
    ) -> list[QueryCondition]:
        """Apply the first comparison ``int_filter`` sets."""
        if int_filter is None:
            return []
        operations: list[tuple[int | None, Callable[[int], QueryCondition]]] = [
            (int_filter.equals, conditions.equals),
            (int_filter.not_equals, conditions.not_equals),
            (int_filter.greater_than, conditions.greater_than),
            (int_filter.greater_than_or_equal, conditions.greater_than_or_equal),
            (int_filter.less_than, conditions.less_than),
            (int_filter.less_than_or_equal, conditions.less_than_or_equal),
        ]
        for value, operation in operations:
            if value is not None:
                return [operation(value)]
        return []

    @final
    def apply_decimal_filter(
        self, decimal_filter: DecimalFilter | None, conditions: DecimalConditions
    ) -> list[QueryCondition]:
        """Apply the first comparison ``decimal_filter`` sets."""
        if decimal_filter is None:
            return []
        operations: list[tuple[Decimal | None, Callable[[Decimal], QueryCondition]]] = [
            (decimal_filter.equals, conditions.equals),
            (decimal_filter.not_equals, conditions.not_equals),
            (decimal_filter.greater_than, conditions.greater_than),
            (decimal_filter.greater_than_or_equal, conditions.greater_than_or_equal),
            (decimal_filter.less_than, conditions.less_than),
            (decimal_filter.less_than_or_equal, conditions.less_than_or_equal),
        ]
        for value, operation in operations:
            if value is not None:
                return [operation(value)]
        return []

    @final
    def apply_enum_filter(
        self, enum_filter: EnumFilter[Any] | None, conditions: EnumConditions[Any]
    ) -> list[QueryCondition]:
        """Apply every operation ``enum_filter`` sets, each as its own condition."""
        if enum_filter is None:
            return []
        applied: list[QueryCondition] = []
        if enum_filter.equals is not None:
            applied.append(conditions.equals(conditions.to_value(enum_filter.equals)))
        if enum_filter.in_ is not None:
            applied.append(conditions.in_([conditions.to_value(v) for v in enum_filter.in_]))
        if enum_filter.not_equals is not None:
            applied.append(conditions.not_equals(conditions.to_value(enum_filter.not_equals)))
        if enum_filter.not_in is not None:
            applied.append(conditions.not_in([conditions.to_value(v) for v in enum_filter.not_in]))
        return applied

    @final
    def apply_bool_filter(
        self, bool_filter: bool | None, conditions: BoolConditions
    ) -> list[QueryCondition]:
        if bool_filter is None:
            return []
        return [conditions.equals(bool_filter)]

    @final
    def apply_to_many_filter[F](
        self,
        to_many_filter: ToManyFilter[F] | None,
        correlation: ToManyCorrelation,
        row_conditions: Callable[[F], list[QueryCondition]],
    ) -> list[QueryCondition]:
        """Apply every quantifier ``to_many_filter`` sets, each as its own condition.

        ``row_conditions`` turns the row filter into the conditions one related row must meet.
        """
        if to_many_filter is None:
            return []
        applied: list[QueryCondition] = []
        if to_many_filter.some is not None:
            applied.append(correlation.some(row_conditions(to_many_filter.some)))
        if to_many_filter.every is not None:
            applied.append(correlation.every(row_conditions(to_many_filter.every)))
        if to_many_filter.none is not None:
            applied.append(correlation.none(row_conditions(to_many_filter.none)))
        return applied
