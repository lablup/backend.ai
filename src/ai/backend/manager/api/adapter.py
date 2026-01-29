"""
Base adapters for converting DTOs to repository query objects.
Provides reusable conversion logic for common patterns.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import final

from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.manager.api.gql.base import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.repositories.base import QueryCondition


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
