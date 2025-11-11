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
    async def test_passthrough_error_propagation_through_handler(self, aiohttp_client) -> None:
        """Test that PassthroughError correctly propagates status code and error code through aiohttp handler."""
        test_error_code = ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.FORBIDDEN,
        )
        test_status_code = HTTPStatus.FORBIDDEN
        test_error_message = "Access denied to storage resource"

        async def error_handler(_request: web.Request) -> web.Response:
            raise PassthroughError(
                status_code=test_status_code.value,
                error_code=test_error_code,
                error_message=test_error_message,
            )

        # Set up aiohttp application
        app = web.Application()
        app.router.add_get("/test-endpoint", error_handler)

        # Create test client
        client = await aiohttp_client(app)
        resp = await client.get("/test-endpoint")

        # Verify passthrough error is correctly propagated
        assert resp.status == test_status_code.value

        response_body = await resp.json()
        assert "error_code" in response_body
        assert response_body["error_code"] == str(test_error_code)

        assert "msg" in response_body
        assert response_body["msg"] == test_error_message
