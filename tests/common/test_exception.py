from http import HTTPStatus

import pytest
from aiohttp import web

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    PassthroughError,
    UserNotFound,
)


class TestBackendAIErrorCode:
    @pytest.mark.asyncio
    async def test_error_code_in_body(self) -> None:
        """Test that error_code() is correctly included in the error body."""
        error = UserNotFound(extra_msg="User with ID 123 not found")

        # Verify error_code is in the body_dict
        assert "error_code" in error.body_dict
        assert error.body_dict["error_code"] == str(error.error_code())

        # Verify the error code format
        error_code = error.error_code()
        assert str(error_code) == str(error.error_code())

    @pytest.mark.asyncio
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
        self, aiohttp_client, status_code, error_code, error_message, expected_error_code_str
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
