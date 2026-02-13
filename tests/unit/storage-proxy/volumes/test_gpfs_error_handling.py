from __future__ import annotations

import dataclasses
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from pytest import FixtureRequest

from ai.backend.storage.errors import ExternalStorageServiceError
from ai.backend.storage.volumes.gpfs.exceptions import (
    GPFSAPIError,
    GPFSConflictError,
    GPFSForbiddenError,
    GPFSInvalidBodyError,
    GPFSNotFoundError,
    GPFSUnauthorizedError,
)
from ai.backend.storage.volumes.gpfs.gpfs_client import base_response_handler


@dataclasses.dataclass(frozen=True)
class ResponseSpec:
    """Minimal spec for creating a mock aiohttp.ClientResponse."""

    status: int
    body: dict[str, Any] | None = None


@dataclasses.dataclass(frozen=True)
class StatusErrorCase:
    """HTTP status code to GPFS exception mapping test case."""

    status: int
    body: dict[str, Any]
    expected_exc: type[Exception]


class TestBaseResponseHandler:
    """Tests for base_response_handler HTTP status code handling."""

    @pytest.fixture
    def response_case(self, request: FixtureRequest) -> ResponseSpec:
        """Parametrized response specification."""
        return cast(ResponseSpec, request.param)

    @pytest.fixture
    async def mock_response(self, response_case: ResponseSpec) -> MagicMock:
        """Create a mock aiohttp.ClientResponse from response_case."""
        response = MagicMock(spec=aiohttp.ClientResponse)
        response.status = response_case.status
        if response_case.body is not None:
            response.json = AsyncMock(return_value=response_case.body)
        else:
            response.json = AsyncMock(
                side_effect=aiohttp.ContentTypeError(MagicMock(), MagicMock())
            )
        return response

    @pytest.mark.parametrize("response_case", [ResponseSpec(status=200, body=None)], indirect=True)
    async def test_2xx_returns_response(self, mock_response: MagicMock) -> None:
        result = await base_response_handler(mock_response)
        assert result is mock_response

    @pytest.mark.parametrize(
        "response_case",
        [
            StatusErrorCase(
                400, {"status": {"code": 400, "message": "Bad Request"}}, GPFSInvalidBodyError
            ),
            StatusErrorCase(
                401, {"status": {"code": 401, "message": "Unauthorized"}}, GPFSUnauthorizedError
            ),
            StatusErrorCase(
                403, {"status": {"code": 403, "message": "Forbidden"}}, GPFSForbiddenError
            ),
            StatusErrorCase(
                404, {"status": {"code": 404, "message": "Not Found"}}, GPFSNotFoundError
            ),
            StatusErrorCase(
                409, {"status": {"code": 409, "message": "Conflict"}}, GPFSConflictError
            ),
            StatusErrorCase(
                422, {"status": {"code": 422, "message": "Unprocessable"}}, GPFSAPIError
            ),
            StatusErrorCase(500, {"error": "server error"}, ExternalStorageServiceError),
        ],
        indirect=True,
    )
    async def test_error_status_raises_correct_exception(
        self, mock_response: MagicMock, response_case: StatusErrorCase
    ) -> None:
        with pytest.raises(response_case.expected_exc):
            await base_response_handler(mock_response)

    @pytest.mark.parametrize(
        "response_case",
        [ResponseSpec(401, {"status": {"code": 401, "message": "Invalid token"}})],
        indirect=True,
    )
    async def test_error_message_includes_response_body(self, mock_response: MagicMock) -> None:
        with pytest.raises(GPFSUnauthorizedError) as exc_info:
            await base_response_handler(mock_response)
        assert "Invalid token" in str(exc_info.value)

    @pytest.mark.parametrize("response_case", [ResponseSpec(401)], indirect=True)
    async def test_non_json_error_body_handled_gracefully(self, mock_response: MagicMock) -> None:
        with pytest.raises(GPFSUnauthorizedError) as exc_info:
            await base_response_handler(mock_response)
        assert "Unable to decode response body" in str(exc_info.value)
