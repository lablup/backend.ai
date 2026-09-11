from __future__ import annotations

import dataclasses
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from pytest import FixtureRequest

from ai.backend.storage.errors import ExternalStorageServiceError
from ai.backend.storage.volumes.gpfs.exceptions import (
    GPFSConflictError,
    GPFSForbiddenError,
    GPFSInternalError,
    GPFSInvalidBodyError,
    GPFSNotFoundError,
    GPFSUnauthorizedError,
)
from ai.backend.storage.volumes.gpfs.gpfs_client import base_response_handler


@dataclasses.dataclass(frozen=True)
class StatusErrorCase:
    """HTTP status code to GPFS exception mapping test case."""

    status: int
    body: dict[str, Any]
    expected_exc: type[Exception]


class TestBaseResponseHandler:
    """Tests for base_response_handler HTTP status code handling."""

    @pytest.fixture
    async def mock_response(self, request: FixtureRequest) -> MagicMock:
        """Create a mock aiohttp.ClientResponse from a parametrized StatusErrorCase."""
        case = cast(StatusErrorCase, request.param)
        response = MagicMock(spec=aiohttp.ClientResponse)
        response.status = case.status
        response.json = AsyncMock(return_value=case.body)
        response.case = case
        return response

    @pytest.mark.parametrize(
        "mock_response",
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
                422, {"status": {"code": 422, "message": "Unprocessable"}}, GPFSInternalError
            ),
            StatusErrorCase(500, {"error": "server error"}, ExternalStorageServiceError),
        ],
        indirect=True,
    )
    async def test_error_status_raises_correct_exception(self, mock_response: MagicMock) -> None:
        with pytest.raises(mock_response.case.expected_exc):
            await base_response_handler(mock_response)
