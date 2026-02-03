"""Tests for GraphQL base utilities including cursor encode/decode."""

from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest
import sqlalchemy as sa
from graphql_relay.utils import base64

from ai.backend.manager.api.gql.base import (
    CURSOR_VERSION,
    StringFilter,
    StringMatchSpec,
    decode_cursor,
    encode_cursor,
)
from ai.backend.manager.errors.api import InvalidCursor
from ai.backend.manager.repositories.base import QueryCondition


class TestEncodeCursor:
    """Tests for encode_cursor function."""

    def test_encode_cursor_with_string_id(self) -> None:
        """Test encoding a string ID to cursor format."""
        cursor = encode_cursor("test-id")
        assert cursor is not None
        assert isinstance(cursor, str)
        # Should be base64 encoded
        assert cursor != "test-id"

    def test_encode_cursor_with_uuid(self) -> None:
        """Test encoding a UUID to cursor format."""
        test_uuid = uuid.uuid4()
        cursor = encode_cursor(test_uuid)
        assert cursor is not None
        assert isinstance(cursor, str)
        # Cursor should contain the UUID string representation
        decoded_id = decode_cursor(cursor)
        assert decoded_id == str(test_uuid)


class TestDecodeCursor:
    """Tests for decode_cursor function."""

    def test_decode_cursor_valid(self) -> None:
        """Test decoding a valid cursor returns the row ID."""
        original_id = "test-row-id-123"
        cursor = encode_cursor(original_id)
        decoded_id = decode_cursor(cursor)
        assert decoded_id == original_id

    def test_decode_cursor_invalid_encoding(self) -> None:
        """Test that invalid base64 encoding raises InvalidCursor."""
        with pytest.raises(InvalidCursor) as exc_info:
            decode_cursor("not-valid-base64!!!")
        # May raise either encoding or format error depending on unbase64 behavior
        assert "Invalid cursor" in str(exc_info.value)

    def test_decode_cursor_invalid_format(self) -> None:
        """Test that wrong format (not cursor:v1:id) raises InvalidCursor."""
        # Valid base64 but wrong format
        invalid_cursor = base64("wrong:format")
        with pytest.raises(InvalidCursor) as exc_info:
            decode_cursor(invalid_cursor)
        assert "Invalid cursor format" in str(exc_info.value)

    def test_decode_cursor_wrong_version(self) -> None:
        """Test that wrong version raises InvalidCursor."""
        # Valid format but wrong version
        invalid_cursor = base64("cursor:v999:some-id")
        with pytest.raises(InvalidCursor) as exc_info:
            decode_cursor(invalid_cursor)
        assert "Invalid cursor format" in str(exc_info.value)

    def test_decode_cursor_missing_parts(self) -> None:
        """Test that cursor with missing parts raises InvalidCursor."""
        # Only two parts instead of three
        invalid_cursor = base64("cursor:v1")
        with pytest.raises(InvalidCursor) as exc_info:
            decode_cursor(invalid_cursor)
        assert "Invalid cursor format" in str(exc_info.value)


class TestCursorRoundtrip:
    """Tests for encode/decode roundtrip behavior."""

    def test_encode_decode_roundtrip_string(self) -> None:
        """Test that encoding then decoding returns original string ID."""
        original_id = "my-scaling-group-name"
        cursor = encode_cursor(original_id)
        decoded_id = decode_cursor(cursor)
        assert decoded_id == original_id

    def test_encode_decode_roundtrip_uuid(self) -> None:
        """Test that encoding then decoding returns original UUID as string."""
        original_uuid = uuid.uuid4()
        cursor = encode_cursor(original_uuid)
        decoded_id = decode_cursor(cursor)
        assert decoded_id == str(original_uuid)

    def test_encode_decode_roundtrip_special_characters(self) -> None:
        """Test roundtrip with special characters in ID."""
        original_id = "test:id:with:colons"
        cursor = encode_cursor(original_id)
        decoded_id = decode_cursor(cursor)
        assert decoded_id == original_id

    def test_cursor_version_constant(self) -> None:
        """Test that CURSOR_VERSION is defined correctly."""
        assert CURSOR_VERSION == "v1"


class TestStringMatchSpec:
    """Tests for StringMatchSpec dataclass."""

    def test_all_values_required(self) -> None:
        """Test that StringMatchSpec requires all three values."""
        spec = StringMatchSpec(value="test", case_insensitive=False, negated=False)
        assert spec.value == "test"
        assert spec.case_insensitive is False
        assert spec.negated is False

    def test_case_insensitive_flag(self) -> None:
        """Test case_insensitive flag."""
        spec = StringMatchSpec(value="test", case_insensitive=True, negated=False)
        assert spec.value == "test"
        assert spec.case_insensitive is True
        assert spec.negated is False

    def test_negated_flag(self) -> None:
        """Test negated flag."""
        spec = StringMatchSpec(value="test", case_insensitive=False, negated=True)
        assert spec.value == "test"
        assert spec.case_insensitive is False
        assert spec.negated is True

    def test_both_flags(self) -> None:
        """Test both case_insensitive and negated flags."""
        spec = StringMatchSpec(value="test", case_insensitive=True, negated=True)
        assert spec.value == "test"
        assert spec.case_insensitive is True
        assert spec.negated is True

    def test_immutability(self) -> None:
        """Test that StringMatchSpec is frozen (immutable)."""
        spec = StringMatchSpec(value="test", case_insensitive=False, negated=False)
        with pytest.raises(AttributeError):
            spec.value = "other"  # type: ignore[misc]


class TestStringFilter:
    """Tests for StringFilter.build_query_condition method."""

    @staticmethod
    def make_factory(
        name: str,
    ) -> tuple[
        list[tuple[str, StringMatchSpec]],
        tuple[
            Callable[[StringMatchSpec], QueryCondition],
            Callable[[StringMatchSpec], QueryCondition],
            Callable[[StringMatchSpec], QueryCondition],
            Callable[[StringMatchSpec], QueryCondition],
        ],
    ]:
        """Create mock factory functions that record their calls.

        Returns a tuple of (call_record, factories) where:
        - call_record: list to record (factory_name, spec) tuples
        - factories: tuple of (contains, equals, starts_with, ends_with) factory functions
        """
        calls: list[tuple[str, StringMatchSpec]] = []

        def make_query_condition(factory_name: str, spec: StringMatchSpec) -> QueryCondition:
            calls.append((factory_name, spec))
            return lambda: sa.literal(True)

        contains_factory = lambda spec: make_query_condition("contains", spec)
        equals_factory = lambda spec: make_query_condition("equals", spec)
        starts_with_factory = lambda spec: make_query_condition("starts_with", spec)
        ends_with_factory = lambda spec: make_query_condition("ends_with", spec)

        return calls, (contains_factory, equals_factory, starts_with_factory, ends_with_factory)

    def test_equals_filter(self) -> None:
        """Test that equals filter produces correct StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(equals="test-value")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "equals"
        assert calls[0][1].value == "test-value"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is False

    def test_i_equals_filter(self) -> None:
        """Test that i_equals filter produces case-insensitive StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_equals="test-value")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "equals"
        assert calls[0][1].value == "test-value"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is False

    def test_not_equals_filter(self) -> None:
        """Test that not_equals filter produces negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(not_equals="test-value")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "equals"
        assert calls[0][1].value == "test-value"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is True

    def test_i_not_equals_filter(self) -> None:
        """Test that i_not_equals produces case-insensitive negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_not_equals="test-value")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "equals"
        assert calls[0][1].value == "test-value"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is True

    def test_contains_filter(self) -> None:
        """Test that contains filter produces correct StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(contains="substring")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "contains"
        assert calls[0][1].value == "substring"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is False

    def test_i_contains_filter(self) -> None:
        """Test that i_contains filter produces case-insensitive StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_contains="substring")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "contains"
        assert calls[0][1].value == "substring"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is False

    def test_starts_with_filter(self) -> None:
        """Test that starts_with filter produces correct StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(starts_with="prefix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "starts_with"
        assert calls[0][1].value == "prefix"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is False

    def test_i_starts_with_filter(self) -> None:
        """Test that i_starts_with produces case-insensitive StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_starts_with="prefix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "starts_with"
        assert calls[0][1].value == "prefix"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is False

    def test_ends_with_filter(self) -> None:
        """Test that ends_with filter produces correct StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(ends_with="suffix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "ends_with"
        assert calls[0][1].value == "suffix"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is False

    def test_i_ends_with_filter(self) -> None:
        """Test that i_ends_with produces case-insensitive StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_ends_with="suffix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "ends_with"
        assert calls[0][1].value == "suffix"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is False

    def test_empty_filter_returns_none(self) -> None:
        """Test that an empty filter returns None."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter()
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is None
        assert len(calls) == 0

    def test_filter_priority_equals_first(self) -> None:
        """Test that equals has priority over contains when both set."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        # When multiple filters are set, equals should take priority
        filter_ = StringFilter(equals="exact", contains="substring")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "equals"
        assert calls[0][1].value == "exact"

    def test_filter_priority_contains_over_starts_with(self) -> None:
        """Test that contains has priority over starts_with when both set."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(contains="substring", starts_with="prefix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "contains"
        assert calls[0][1].value == "substring"

    def test_filter_priority_starts_with_over_ends_with(self) -> None:
        """Test that starts_with has priority over ends_with when both set."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(starts_with="prefix", ends_with="suffix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "starts_with"
        assert calls[0][1].value == "prefix"

    def test_not_contains_filter(self) -> None:
        """Test that not_contains filter produces negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(not_contains="substring")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "contains"
        assert calls[0][1].value == "substring"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is True

    def test_i_not_contains_filter(self) -> None:
        """Test that i_not_contains produces case-insensitive negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_not_contains="substring")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "contains"
        assert calls[0][1].value == "substring"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is True

    def test_not_starts_with_filter(self) -> None:
        """Test that not_starts_with filter produces negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(not_starts_with="prefix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "starts_with"
        assert calls[0][1].value == "prefix"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is True

    def test_i_not_starts_with_filter(self) -> None:
        """Test that i_not_starts_with produces case-insensitive negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_not_starts_with="prefix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "starts_with"
        assert calls[0][1].value == "prefix"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is True

    def test_not_ends_with_filter(self) -> None:
        """Test that not_ends_with filter produces negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(not_ends_with="suffix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "ends_with"
        assert calls[0][1].value == "suffix"
        assert calls[0][1].case_insensitive is False
        assert calls[0][1].negated is True

    def test_i_not_ends_with_filter(self) -> None:
        """Test that i_not_ends_with produces case-insensitive negated StringMatchSpec."""
        calls, (contains_f, equals_f, starts_with_f, ends_with_f) = self.make_factory("test")
        filter_ = StringFilter(i_not_ends_with="suffix")
        result = filter_.build_query_condition(
            contains_factory=contains_f,
            equals_factory=equals_f,
            starts_with_factory=starts_with_f,
            ends_with_factory=ends_with_f,
        )
        assert result is not None
        assert len(calls) == 1
        assert calls[0][0] == "ends_with"
        assert calls[0][1].value == "suffix"
        assert calls[0][1].case_insensitive is True
        assert calls[0][1].negated is True
