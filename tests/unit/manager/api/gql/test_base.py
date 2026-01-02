"""Tests for GraphQL base utilities including cursor encode/decode."""

from __future__ import annotations

import uuid

import pytest

from ai.backend.manager.api.gql.base import CURSOR_VERSION, decode_cursor, encode_cursor
from ai.backend.manager.errors.api import InvalidCursor


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
        from graphql_relay.utils import base64

        # Valid base64 but wrong format
        invalid_cursor = base64("wrong:format")
        with pytest.raises(InvalidCursor) as exc_info:
            decode_cursor(invalid_cursor)
        assert "Invalid cursor format" in str(exc_info.value)

    def test_decode_cursor_wrong_version(self) -> None:
        """Test that wrong version raises InvalidCursor."""
        from graphql_relay.utils import base64

        # Valid format but wrong version
        invalid_cursor = base64("cursor:v999:some-id")
        with pytest.raises(InvalidCursor) as exc_info:
            decode_cursor(invalid_cursor)
        assert "Invalid cursor format" in str(exc_info.value)

    def test_decode_cursor_missing_parts(self) -> None:
        """Test that cursor with missing parts raises InvalidCursor."""
        from graphql_relay.utils import base64

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
