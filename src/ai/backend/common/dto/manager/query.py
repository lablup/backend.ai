from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date, datetime
from typing import TypeVar

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec

_QC = TypeVar("_QC")


class DateTimeRangeFilter(BaseRequestModel):
    """
    Filters records by a datetime range.

    Both boundaries are inclusive. You can specify just 'after', just 'before',
    or both to define the range. Records matching the boundary values are included.
    This filter is shared across all report types for datetime fields like
    created_at, modified_at, terminated_at, etc.
    """

    after: datetime | None = Field(
        default=None,
        description=(
            "Include only records created on or after this datetime. "
            "Should be in ISO 8601 format (e.g., '2024-01-01T00:00:00Z'). "
            "If not specified, there is no lower bound on the datetime range."
        ),
    )
    before: datetime | None = Field(
        default=None,
        description=(
            "Include only records created on or before this datetime. "
            "Should be in ISO 8601 format (e.g., '2024-12-31T23:59:59Z'). "
            "If not specified, there is no upper bound on the datetime range."
        ),
    )


class DateRangeFilter(BaseRequestModel):
    """
    Filters records by a date range.

    Both boundaries are inclusive. You can specify just 'after', just 'before',
    or both to define the range. Records matching the boundary values are included.
    This filter is used for date fields like period_start in usage buckets.
    """

    after: date | None = Field(
        default=None,
        description=(
            "Include only records with dates on or after this date. "
            "Should be in ISO 8601 date format (e.g., '2024-01-01'). "
            "If not specified, there is no lower bound on the date range."
        ),
    )
    before: date | None = Field(
        default=None,
        description=(
            "Include only records with dates on or before this date. "
            "Should be in ISO 8601 date format (e.g., '2024-12-31'). "
            "If not specified, there is no upper bound on the date range."
        ),
    )


class StringFilter(BaseRequestModel):
    """Comprehensive string field filter supporting multiple match operations.

    Provides flexible string matching with four operation types (equals, contains,
    starts_with, ends_with), each available in case-sensitive, case-insensitive,
    and negated variants for complete filtering control.
    """

    # Basic operations (case-sensitive)
    equals: str | None = Field(default=None, description="Exact match (case-sensitive)")
    contains: str | None = Field(default=None, description="Contains (case-sensitive)")
    starts_with: str | None = Field(default=None, description="Starts with (case-sensitive)")
    ends_with: str | None = Field(default=None, description="Ends with (case-sensitive)")

    # NOT operations (case-sensitive)
    not_equals: str | None = Field(default=None, description="Not equals (case-sensitive)")
    not_contains: str | None = Field(default=None, description="Not contains (case-sensitive)")
    not_starts_with: str | None = Field(
        default=None, description="Not starts with (case-sensitive)"
    )
    not_ends_with: str | None = Field(default=None, description="Not ends with (case-sensitive)")

    # Case-insensitive operations
    i_equals: str | None = Field(default=None, description="Exact match (case-insensitive)")
    i_contains: str | None = Field(default=None, description="Contains (case-insensitive)")
    i_starts_with: str | None = Field(default=None, description="Starts with (case-insensitive)")
    i_ends_with: str | None = Field(default=None, description="Ends with (case-insensitive)")

    # Case-insensitive NOT operations
    i_not_equals: str | None = Field(default=None, description="Not equals (case-insensitive)")
    i_not_contains: str | None = Field(default=None, description="Not contains (case-insensitive)")
    i_not_starts_with: str | None = Field(
        default=None, description="Not starts with (case-insensitive)"
    )
    i_not_ends_with: str | None = Field(
        default=None, description="Not ends with (case-insensitive)"
    )

    def build_query_condition(
        self,
        contains_factory: Callable[[StringMatchSpec], _QC],
        equals_factory: Callable[[StringMatchSpec], _QC],
        starts_with_factory: Callable[[StringMatchSpec], _QC],
        ends_with_factory: Callable[[StringMatchSpec], _QC],
    ) -> _QC | None:
        """Build a query condition from this filter using the provided factory callables.

        Args:
            contains_factory: Factory for LIKE '%value%' operations
            equals_factory: Factory for exact match (=) operations
            starts_with_factory: Factory for LIKE 'value%' operations
            ends_with_factory: Factory for LIKE '%value' operations

        Returns:
            _QC if any filter field is set, None otherwise
        """
        # equals operations
        if self.equals is not None:
            return equals_factory(
                StringMatchSpec(self.equals, case_insensitive=False, negated=False)
            )
        if self.i_equals is not None:
            return equals_factory(
                StringMatchSpec(self.i_equals, case_insensitive=True, negated=False)
            )
        if self.not_equals is not None:
            return equals_factory(
                StringMatchSpec(self.not_equals, case_insensitive=False, negated=True)
            )
        if self.i_not_equals is not None:
            return equals_factory(
                StringMatchSpec(self.i_not_equals, case_insensitive=True, negated=True)
            )

        # contains operations
        if self.contains is not None:
            return contains_factory(
                StringMatchSpec(self.contains, case_insensitive=False, negated=False)
            )
        if self.i_contains is not None:
            return contains_factory(
                StringMatchSpec(self.i_contains, case_insensitive=True, negated=False)
            )
        if self.not_contains is not None:
            return contains_factory(
                StringMatchSpec(self.not_contains, case_insensitive=False, negated=True)
            )
        if self.i_not_contains is not None:
            return contains_factory(
                StringMatchSpec(self.i_not_contains, case_insensitive=True, negated=True)
            )

        # starts_with operations
        if self.starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(self.starts_with, case_insensitive=False, negated=False)
            )
        if self.i_starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(self.i_starts_with, case_insensitive=True, negated=False)
            )
        if self.not_starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(self.not_starts_with, case_insensitive=False, negated=True)
            )
        if self.i_not_starts_with is not None:
            return starts_with_factory(
                StringMatchSpec(self.i_not_starts_with, case_insensitive=True, negated=True)
            )

        # ends_with operations
        if self.ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(self.ends_with, case_insensitive=False, negated=False)
            )
        if self.i_ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(self.i_ends_with, case_insensitive=True, negated=False)
            )
        if self.not_ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(self.not_ends_with, case_insensitive=False, negated=True)
            )
        if self.i_not_ends_with is not None:
            return ends_with_factory(
                StringMatchSpec(self.i_not_ends_with, case_insensitive=True, negated=True)
            )

        return None


class UUIDFilter(BaseRequestModel):
    """Filter for UUID fields supporting equality and set operations.

    Provides UUID matching with equals/not_equals and in/not_in operations.
    """

    # Basic operations
    equals: uuid.UUID | None = Field(default=None, description="Exact UUID match")
    in_: list[uuid.UUID] | None = Field(default=None, alias="in", description="UUID is in list")

    # NOT operations
    not_equals: uuid.UUID | None = Field(default=None, description="Not equals UUID")
    not_in: list[uuid.UUID] | None = Field(default=None, description="UUID is not in list")

    def build_query_condition(
        self,
        equals_factory: Callable[[UUIDEqualMatchSpec], _QC],
        in_factory: Callable[[UUIDInMatchSpec], _QC],
    ) -> _QC | None:
        """Build a query condition from this filter using the provided factory callables.

        Args:
            equals_factory: Factory function for equality operations (=, !=)
            in_factory: Factory function for IN operations (IN, NOT IN)

        Returns:
            _QC if any filter field is set, None otherwise
        """
        if self.equals is not None:
            return equals_factory(UUIDEqualMatchSpec(value=self.equals, negated=False))
        if self.not_equals is not None:
            return equals_factory(UUIDEqualMatchSpec(value=self.not_equals, negated=True))
        if self.in_ is not None:
            return in_factory(UUIDInMatchSpec(values=self.in_, negated=False))
        if self.not_in is not None:
            return in_factory(UUIDInMatchSpec(values=self.not_in, negated=True))
        return None


class ListGroupQuery(BaseRequestModel):
    group_id: uuid.UUID | None = Field(default=None, alias="groupId")
