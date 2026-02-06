from __future__ import annotations

from ai.backend.common.middlewares.request_id import _sanitize_client_operation


class TestSanitizeClientOperation:
    def test_valid_operation(self) -> None:
        assert _sanitize_client_operation("create_session") == "create_session"

    def test_valid_operation_with_dots_and_colons(self) -> None:
        assert _sanitize_client_operation("api:v2.list-sessions") == "api:v2.list-sessions"

    def test_empty_string(self) -> None:
        assert _sanitize_client_operation("") == ""

    def test_operation_with_spaces_rejected(self) -> None:
        assert _sanitize_client_operation("invalid operation") == ""

    def test_operation_with_special_chars_rejected(self) -> None:
        assert _sanitize_client_operation("op;DROP TABLE") == ""

    def test_operation_truncated_to_max_length(self) -> None:
        long_op = "a" * 100
        result = _sanitize_client_operation(long_op)
        assert len(result) == 64
        assert result == "a" * 64

    def test_operation_with_unicode_rejected(self) -> None:
        assert _sanitize_client_operation("op\u00e9ration") == ""
