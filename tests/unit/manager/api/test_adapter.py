"""
Tests for base adapter classes.
Tests conversion utilities for common filter patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.dto.manager.notification import StringFilter
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base import QueryCondition

if TYPE_CHECKING:
    from sqlalchemy.sql.expression import ColumnElement


class TestBaseFilterAdapter:
    """Test cases for BaseFilterAdapter"""

    def test_convert_string_filter_equals(self) -> None:
        """Test string filter conversion with equals"""
        string_filter = StringFilter(equals="test value")
        adapter = BaseFilterAdapter()

        # Mock conversion functions to verify they are called correctly
        called_with: dict[str, tuple[str, bool]] = {}

        def equals_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["equals"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def contains_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["contains"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        result = adapter.convert_string_filter(string_filter, equals_fn, contains_fn)

        assert result is not None
        assert "equals" in called_with
        assert called_with["equals"] == ("test value", False)
        assert "contains" not in called_with

    def test_convert_string_filter_i_equals(self) -> None:
        """Test string filter conversion with case-insensitive equals"""
        string_filter = StringFilter(i_equals="test value")
        adapter = BaseFilterAdapter()

        called_with: dict[str, tuple[str, bool]] = {}

        def equals_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["equals"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def contains_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["contains"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        result = adapter.convert_string_filter(string_filter, equals_fn, contains_fn)

        assert result is not None
        assert "equals" in called_with
        assert called_with["equals"] == ("test value", True)
        assert "contains" not in called_with

    def test_convert_string_filter_contains(self) -> None:
        """Test string filter conversion with contains"""
        string_filter = StringFilter(contains="test")
        adapter = BaseFilterAdapter()

        called_with: dict[str, tuple[str, bool]] = {}

        def equals_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["equals"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def contains_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["contains"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        result = adapter.convert_string_filter(string_filter, equals_fn, contains_fn)

        assert result is not None
        assert "contains" in called_with
        assert called_with["contains"] == ("test", False)
        assert "equals" not in called_with

    def test_convert_string_filter_i_contains(self) -> None:
        """Test string filter conversion with case-insensitive contains"""
        string_filter = StringFilter(i_contains="test")
        adapter = BaseFilterAdapter()

        called_with: dict[str, tuple[str, bool]] = {}

        def equals_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["equals"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def contains_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["contains"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        result = adapter.convert_string_filter(string_filter, equals_fn, contains_fn)

        assert result is not None
        assert "contains" in called_with
        assert called_with["contains"] == ("test", True)
        assert "equals" not in called_with

    def test_convert_string_filter_empty(self) -> None:
        """Test string filter conversion with no values set"""
        string_filter = StringFilter()
        adapter = BaseFilterAdapter()

        called_with: dict[str, tuple[str, bool]] = {}

        def equals_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["equals"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def contains_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["contains"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        result = adapter.convert_string_filter(string_filter, equals_fn, contains_fn)

        assert result is None
        assert len(called_with) == 0

    def test_convert_string_filter_priority(self) -> None:
        """Test that equals has priority over contains when both are set"""
        # This shouldn't happen in practice due to pydantic validation,
        # but test the priority order anyway
        string_filter = StringFilter(equals="exact", contains="partial")
        adapter = BaseFilterAdapter()

        called_with: dict[str, tuple[str, bool]] = {}

        def equals_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["equals"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def contains_fn(value: str, case_insensitive: bool) -> QueryCondition:
            called_with["contains"] = (value, case_insensitive)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        result = adapter.convert_string_filter(string_filter, equals_fn, contains_fn)

        assert result is not None
        # equals should be called, not contains
        assert "equals" in called_with
        assert called_with["equals"] == ("exact", False)
        assert "contains" not in called_with
