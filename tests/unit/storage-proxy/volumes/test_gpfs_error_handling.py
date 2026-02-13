from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.common.exception import BackendAIError, ErrorDetail, ErrorDomain, ErrorOperation
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


def _mock_response(status: int, json_body: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock aiohttp.ClientResponse with given status and JSON body."""
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = status
    if json_body is not None:
        response.json = AsyncMock(return_value=json_body)
    else:
        response.json = AsyncMock(
            side_effect=aiohttp.ContentTypeError(
                MagicMock(),
                MagicMock(),
            )
        )
    return response


class TestBaseResponseHandler:
    """Tests for base_response_handler HTTP status code handling."""

    @pytest.mark.asyncio
    async def test_2xx_returns_response(self) -> None:
        response = _mock_response(200)
        result = await base_response_handler(response)
        assert result is response

    @pytest.mark.asyncio
    async def test_401_raises_gpfs_unauthorized_error(self) -> None:
        response = _mock_response(401, {"status": {"code": 401, "message": "Unauthorized"}})
        with pytest.raises(GPFSUnauthorizedError):
            await base_response_handler(response)

    @pytest.mark.asyncio
    async def test_400_raises_gpfs_invalid_body_error(self) -> None:
        response = _mock_response(400, {"status": {"code": 400, "message": "Bad Request"}})
        with pytest.raises(GPFSInvalidBodyError):
            await base_response_handler(response)

    @pytest.mark.asyncio
    async def test_403_raises_gpfs_forbidden_error(self) -> None:
        response = _mock_response(403, {"status": {"code": 403, "message": "Forbidden"}})
        with pytest.raises(GPFSForbiddenError):
            await base_response_handler(response)

    @pytest.mark.asyncio
    async def test_404_raises_gpfs_not_found_error(self) -> None:
        response = _mock_response(404, {"status": {"code": 404, "message": "Not Found"}})
        with pytest.raises(GPFSNotFoundError):
            await base_response_handler(response)

    @pytest.mark.asyncio
    async def test_409_raises_gpfs_conflict_error(self) -> None:
        response = _mock_response(409, {"status": {"code": 409, "message": "Conflict"}})
        with pytest.raises(GPFSConflictError):
            await base_response_handler(response)

    @pytest.mark.asyncio
    async def test_other_4xx_raises_gpfs_api_error(self) -> None:
        response = _mock_response(422, {"status": {"code": 422, "message": "Unprocessable"}})
        with pytest.raises(GPFSAPIError):
            await base_response_handler(response)

    @pytest.mark.asyncio
    async def test_5xx_raises_external_storage_service_error(self) -> None:
        response = _mock_response(500, {"error": "server error"})
        with pytest.raises(ExternalStorageServiceError):
            await base_response_handler(response)

    @pytest.mark.asyncio
    async def test_error_message_includes_response_body(self) -> None:
        body = {"status": {"code": 401, "message": "Invalid token"}}
        response = _mock_response(401, body)
        with pytest.raises(GPFSUnauthorizedError) as exc_info:
            await base_response_handler(response)
        assert "Invalid token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_non_json_error_body_handled_gracefully(self) -> None:
        response = _mock_response(401, json_body=None)
        with pytest.raises(GPFSUnauthorizedError) as exc_info:
            await base_response_handler(response)
        assert "Unable to decode response body" in str(exc_info.value)


class TestGPFSExceptionHierarchy:
    """Tests that GPFS API exceptions follow BackendAIError pattern."""

    def test_api_errors_are_backend_ai_errors(self) -> None:
        assert issubclass(GPFSAPIError, BackendAIError)
        assert issubclass(GPFSUnauthorizedError, BackendAIError)
        assert issubclass(GPFSNotFoundError, BackendAIError)

    def test_unauthorized_error_has_correct_error_code(self) -> None:
        err = GPFSUnauthorizedError(extra_msg="test")
        code = err.error_code()
        assert code.domain == ErrorDomain.STORAGE
        assert code.operation == ErrorOperation.AUTH
        assert code.error_detail == ErrorDetail.UNAUTHORIZED

    def test_not_found_error_has_correct_error_code(self) -> None:
        err = GPFSNotFoundError(extra_msg="test")
        code = err.error_code()
        assert code.domain == ErrorDomain.STORAGE
        assert code.operation == ErrorOperation.READ
        assert code.error_detail == ErrorDetail.NOT_FOUND

    def test_error_code_included_in_body(self) -> None:
        err = GPFSUnauthorizedError(extra_msg="test auth failure")
        assert "error_code" in err.body_dict
        assert err.body_dict["error_code"] == "storage_auth_unauthorized"
