"""
Tests for base adapter classes.
Tests conversion utilities for common filter patterns.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.repositories.base import QueryCondition

if TYPE_CHECKING:
    from sqlalchemy.sql.expression import ColumnElement


@dataclass
class CapturedSpec:
    """Captured StringMatchSpec for verification."""

    value: str
    case_insensitive: bool
    negated: bool


class TestBaseFilterAdapter:
    """Test cases for BaseFilterAdapter"""

    def _create_mock_factories(
        self, called_with: dict[str, CapturedSpec]
    ) -> tuple[
        Callable[[StringMatchSpec], QueryCondition],
        Callable[[StringMatchSpec], QueryCondition],
        Callable[[StringMatchSpec], QueryCondition],
        Callable[[StringMatchSpec], QueryCondition],
    ]:
        """Create mock factory functions that capture the StringMatchSpec."""

        def contains_factory(spec: StringMatchSpec) -> QueryCondition:
            called_with["contains"] = CapturedSpec(spec.value, spec.case_insensitive, spec.negated)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def equals_factory(spec: StringMatchSpec) -> QueryCondition:
            called_with["equals"] = CapturedSpec(spec.value, spec.case_insensitive, spec.negated)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def starts_with_factory(spec: StringMatchSpec) -> QueryCondition:
            called_with["starts_with"] = CapturedSpec(
                spec.value, spec.case_insensitive, spec.negated
            )

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        def ends_with_factory(spec: StringMatchSpec) -> QueryCondition:
            called_with["ends_with"] = CapturedSpec(spec.value, spec.case_insensitive, spec.negated)

            def condition() -> ColumnElement[bool]:
                return sa.literal(True)

            return condition

        return contains_factory, equals_factory, starts_with_factory, ends_with_factory

    def test_convert_string_filter_equals(self) -> None:
        """Test string filter conversion with equals"""
        string_filter = StringFilter(equals="test value")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "equals" in called_with
        assert called_with["equals"].value == "test value"
        assert called_with["equals"].case_insensitive is False
        assert called_with["equals"].negated is False

    def test_convert_string_filter_i_equals(self) -> None:
        """Test string filter conversion with case-insensitive equals"""
        string_filter = StringFilter(i_equals="test value")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "equals" in called_with
        assert called_with["equals"].value == "test value"
        assert called_with["equals"].case_insensitive is True
        assert called_with["equals"].negated is False

    def test_convert_string_filter_not_equals(self) -> None:
        """Test string filter conversion with negated equals"""
        string_filter = StringFilter(not_equals="test value")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "equals" in called_with
        assert called_with["equals"].value == "test value"
        assert called_with["equals"].case_insensitive is False
        assert called_with["equals"].negated is True

    def test_convert_string_filter_i_not_equals(self) -> None:
        """Test string filter conversion with case-insensitive negated equals"""
        string_filter = StringFilter(i_not_equals="test value")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "equals" in called_with
        assert called_with["equals"].value == "test value"
        assert called_with["equals"].case_insensitive is True
        assert called_with["equals"].negated is True

    def test_convert_string_filter_contains(self) -> None:
        """Test string filter conversion with contains"""
        string_filter = StringFilter(contains="test")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "contains" in called_with
        assert called_with["contains"].value == "test"
        assert called_with["contains"].case_insensitive is False
        assert called_with["contains"].negated is False

    def test_convert_string_filter_i_contains(self) -> None:
        """Test string filter conversion with case-insensitive contains"""
        string_filter = StringFilter(i_contains="test")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "contains" in called_with
        assert called_with["contains"].value == "test"
        assert called_with["contains"].case_insensitive is True
        assert called_with["contains"].negated is False

    def test_convert_string_filter_not_contains(self) -> None:
        """Test string filter conversion with negated contains"""
        string_filter = StringFilter(not_contains="test")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "contains" in called_with
        assert called_with["contains"].value == "test"
        assert called_with["contains"].case_insensitive is False
        assert called_with["contains"].negated is True

    def test_convert_string_filter_starts_with(self) -> None:
        """Test string filter conversion with starts_with"""
        string_filter = StringFilter(starts_with="pre")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "starts_with" in called_with
        assert called_with["starts_with"].value == "pre"
        assert called_with["starts_with"].case_insensitive is False
        assert called_with["starts_with"].negated is False

    def test_convert_string_filter_i_starts_with(self) -> None:
        """Test string filter conversion with case-insensitive starts_with"""
        string_filter = StringFilter(i_starts_with="pre")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "starts_with" in called_with
        assert called_with["starts_with"].value == "pre"
        assert called_with["starts_with"].case_insensitive is True
        assert called_with["starts_with"].negated is False

    def test_convert_string_filter_ends_with(self) -> None:
        """Test string filter conversion with ends_with"""
        string_filter = StringFilter(ends_with="suffix")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "ends_with" in called_with
        assert called_with["ends_with"].value == "suffix"
        assert called_with["ends_with"].case_insensitive is False
        assert called_with["ends_with"].negated is False

    def test_convert_string_filter_i_ends_with(self) -> None:
        """Test string filter conversion with case-insensitive ends_with"""
        string_filter = StringFilter(i_ends_with="suffix")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        assert "ends_with" in called_with
        assert called_with["ends_with"].value == "suffix"
        assert called_with["ends_with"].case_insensitive is True
        assert called_with["ends_with"].negated is False

    def test_convert_string_filter_empty(self) -> None:
        """Test string filter conversion with no values set"""
        string_filter = StringFilter()
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is None
        assert len(called_with) == 0

    def test_convert_string_filter_priority(self) -> None:
        """Test that equals has priority over contains when both are set"""
        # This shouldn't happen in practice due to pydantic validation,
        # but test the priority order anyway
        string_filter = StringFilter(equals="exact", contains="partial")
        adapter = BaseFilterAdapter()
        called_with: dict[str, CapturedSpec] = {}
        factories = self._create_mock_factories(called_with)

        result = adapter.convert_string_filter(string_filter, *factories)

        assert result is not None
        # equals should be called, not contains
        assert "equals" in called_with
        assert called_with["equals"].value == "exact"
        assert called_with["equals"].case_insensitive is False
        assert called_with["equals"].negated is False
        assert "contains" not in called_with
