"""
Base adapters for converting DTOs to repository query objects.
Provides reusable conversion logic for common patterns.
"""

from __future__ import annotations

from typing import Callable, Optional

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.manager.repositories.base import QueryCondition


class BaseFilterAdapter:
    """Base adapter providing common filter conversion utilities."""

    def convert_string_filter(
        self,
        string_filter: StringFilter,
        equals_fn: Callable[[str, bool], QueryCondition],
        contains_fn: Callable[[str, bool], QueryCondition],
    ) -> Optional[QueryCondition]:
        """
        Convert StringFilter to QueryCondition using provided conversion functions.

        Args:
            string_filter: The string filter to convert
            equals_fn: Function to create equals condition (value, case_insensitive) -> QueryCondition
            contains_fn: Function to create contains condition (value, case_insensitive) -> QueryCondition

        Returns:
            QueryCondition if filter has value, None otherwise
        """
        if string_filter.equals is not None:
            return equals_fn(string_filter.equals, False)
        elif string_filter.i_equals is not None:
            return equals_fn(string_filter.i_equals, True)
        elif string_filter.contains is not None:
            return contains_fn(string_filter.contains, False)
        elif string_filter.i_contains is not None:
            return contains_fn(string_filter.i_contains, True)
        return None
