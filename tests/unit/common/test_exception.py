from __future__ import annotations

from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Any, NamedTuple

import pytest
from aiohttp import web
from pydantic import BaseModel, ValidationError

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    PassthroughError,
    UserNotFound,
    format_pydantic_loc,
    format_pydantic_validation_errors,
)


class _DummyAddress(BaseModel):
    city: str
    zipcode: int


class _DummyUser(BaseModel):
    """A throwaway model used to provoke ``ValidationError`` shapes the
    formatter is expected to handle: top-level fields, nested fields,
    and list-indexed fields."""

    name: str
    age: int
    address: _DummyAddress
    tags: list[str]


def _make_validation_error(payload: dict[str, Any]) -> ValidationError:
    try:
        _DummyUser.model_validate(payload)
    except ValidationError as e:
        return e
    raise AssertionError("Expected ValidationError but model validated successfully")


class _LocCase(NamedTuple):
    """A single ``format_pydantic_loc`` test case: input loc tuple,
    optional location prefix, and the expected rendered string."""

    loc: tuple[Any, ...]
    prefix: str | None
    expected: str


class TestBackendAIErrorCode:
    async def test_error_code_in_body(self) -> None:
        """Test that error_code() is correctly included in the error body."""
        error = UserNotFound(extra_msg="User with ID 123 not found")

        # Verify error_code is in the body_dict
        assert "error_code" in error.body_dict
        assert error.body_dict["error_code"] == str(error.error_code())

        # Verify the error code format
        error_code = error.error_code()
        assert str(error_code) == str(error.error_code())

    @pytest.mark.parametrize(
        "status_code,error_code,error_message,expected_error_code_str",
        [
            (
                HTTPStatus.FORBIDDEN,
                ErrorCode(
                    domain=ErrorDomain.STORAGE,
                    operation=ErrorOperation.READ,
                    error_detail=ErrorDetail.FORBIDDEN,
                ),
                "Access denied to storage resource",
                "storage_read_forbidden",
            ),
            (
                HTTPStatus.REQUEST_TIMEOUT,
                ErrorCode(
                    domain=ErrorDomain.AGENT,
                    operation=ErrorOperation.REQUEST,
                    error_detail=ErrorDetail.TASK_TIMEOUT,
                ),
                "Agent request timed out",
                "agent_request_task-timeout",
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                ErrorCode(
                    domain=ErrorDomain.STORAGE_PROXY,
                    operation=ErrorOperation.REQUEST,
                    error_detail=ErrorDetail.INTERNAL_ERROR,
                ),
                "Internal error from storage proxy",
                "storage-proxy_request_internal-error",
            ),
        ],
    )
    async def test_passthrough_error_propagation_through_handler(
        self,
        aiohttp_client: Callable[[Any], Awaitable[Any]],
        status_code: HTTPStatus,
        error_code: ErrorCode,
        error_message: str,
        expected_error_code_str: str,
    ) -> None:
        """Test that PassthroughError correctly propagates status code and error code through aiohttp handler."""

        async def error_handler(_request: web.Request) -> web.Response:
            raise PassthroughError(
                status_code=status_code.value,
                error_code=error_code,
                error_message=error_message,
            )

        # Set up aiohttp application
        app = web.Application()
        app.router.add_get("/test-endpoint", error_handler)

        # Create test client
        client = await aiohttp_client(app)
        resp = await client.get("/test-endpoint")

        # Verify status code is correctly propagated
        assert resp.status == status_code.value

        # Verify response body contains error information
        response_body = await resp.json()
        assert "error_code" in response_body
        assert response_body["error_code"] == str(error_code)
        assert response_body["error_code"] == expected_error_code_str

        # Verify error message is included
        assert "msg" in response_body
        assert response_body["msg"] == error_message

        # Verify error type and title
        assert "type" in response_body
        assert response_body["type"] == "https://api.backend.ai/probs/forwarded-error"
        assert "title" in response_body
        assert response_body["title"] == "Forwarded Error from Downstream Service"

        # Verify content type is application/problem+json
        assert resp.content_type == "application/problem+json"


class TestFormatPydanticLoc:
    @pytest.mark.parametrize(
        "case",
        [
            # Empty loc renders as <root>
            _LocCase(loc=(), prefix=None, expected="<root>"),
            # Empty loc with a prefix shows just the prefix
            _LocCase(loc=(), prefix="body", expected="body"),
            # Single string field
            _LocCase(loc=("name",), prefix=None, expected="name"),
            # Nested string fields are dotted
            _LocCase(loc=("address", "city"), prefix=None, expected="address.city"),
            # Integer index uses bracket notation
            _LocCase(loc=("tags", 0), prefix=None, expected="tags[0]"),
            # Mix of nested fields and index
            _LocCase(loc=("users", 2, "email"), prefix=None, expected="users[2].email"),
            # Prefix is prepended
            _LocCase(loc=("name",), prefix="body", expected="body.name"),
            _LocCase(loc=("address", "city"), prefix="body", expected="body.address.city"),
            _LocCase(loc=("tags", 0), prefix="body", expected="body.tags[0]"),
            # Leading int with prefix still uses bracket notation
            _LocCase(loc=(0, "name"), prefix="body", expected="body[0].name"),
        ],
    )
    def test_format_pydantic_loc(self, case: _LocCase) -> None:
        assert format_pydantic_loc(case.loc, case.prefix) == case.expected


class TestFormatPydanticValidationErrors:
    def test_single_missing_field_summary(self) -> None:
        exc = _make_validation_error({
            "age": 30,
            "address": {"city": "Seoul", "zipcode": 12345},
            "tags": [],
        })

        summary, structured = format_pydantic_validation_errors(exc)

        assert summary == "name: Field required"
        assert len(structured) == 1
        entry = structured[0]
        assert entry["loc"] == "name"
        assert entry["msg"] == "Field required"
        assert entry["type"] == "missing"

    def test_multiple_errors_joined_with_semicolon(self) -> None:
        exc = _make_validation_error({"name": "Alice", "age": "not-a-number"})

        summary, structured = format_pydantic_validation_errors(exc)

        # Multiple errors are joined with "; " in deterministic Pydantic order
        assert "; " in summary
        # Every per-field error must surface in both summary and structured list
        locs = [entry["loc"] for entry in structured]
        assert "age" in locs
        assert "address" in locs
        for entry in structured:
            assert f"{entry['loc']}: {entry['msg']}" in summary

    def test_nested_and_indexed_locs(self) -> None:
        exc = _make_validation_error({
            "name": "Alice",
            "age": 30,
            "address": {"city": "Seoul", "zipcode": "not-a-number"},
            "tags": ["ok", 123],
        })

        _, structured = format_pydantic_validation_errors(exc)

        locs = {entry["loc"] for entry in structured}
        # Nested field renders dotted
        assert "address.zipcode" in locs
        # List index renders with bracket notation
        assert "tags[1]" in locs

    def test_location_prefix_is_prepended(self) -> None:
        exc = _make_validation_error({
            "age": 30,
            "address": {"city": "Seoul", "zipcode": 12345},
            "tags": [],
        })

        summary, structured = format_pydantic_validation_errors(exc, location_prefix="body")

        assert summary.startswith("body.name:")
        assert structured[0]["loc"] == "body.name"

    def test_input_repr_is_truncated(self) -> None:
        long_value = "x" * 500
        exc = _make_validation_error({
            "name": "Alice",
            "age": long_value,  # str → int validation fails, large input echoed back
            "address": {"city": "Seoul", "zipcode": 12345},
            "tags": [],
        })

        _, structured = format_pydantic_validation_errors(exc)
        age_entry = next(e for e in structured if e["loc"] == "age")
        assert "input" in age_entry
        assert age_entry["input"].endswith("...<truncated>")
        # The truncation cap is 200 chars before the marker
        assert len(age_entry["input"]) <= 200 + len("...<truncated>")

    def test_empty_payload_produces_field_required_summary(self) -> None:
        # Sanity check: a wholly empty payload still produces a real
        # summary (no <root> fallback) because every required field
        # surfaces an individual error.
        exc = _make_validation_error({})
        summary, structured = format_pydantic_validation_errors(exc)
        assert summary != "validation failed"
        assert all(entry["msg"] == "Field required" for entry in structured)
