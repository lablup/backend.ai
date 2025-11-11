import pytest
from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    InvalidAPIParameters,
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
    async def test_multiple_instances_have_same_error_code(self) -> None:
        """Test that different instances of the same error class return the same error code."""
        error1 = InvalidAPIParameters(extra_msg="Missing parameter: foo")
        error2 = InvalidAPIParameters(extra_msg="Missing parameter: bar")

        # Both instances should return the same error code
        assert error1.error_code() == error2.error_code()
        assert str(error1.error_code()) == str(error2.error_code())

    @pytest.mark.asyncio
    async def test_custom_error_subclass(self) -> None:
        """Test creating a custom error subclass with instance method error_code()."""

        class CustomTestError(BackendAIError, web.HTTPBadRequest):
            error_type = "https://api.backend.ai/probs/test-error"
            error_title = "Test Error"

            def error_code(self) -> ErrorCode:
                return ErrorCode(
                    domain=ErrorDomain.BACKENDAI,
                    operation=ErrorOperation.GENERIC,
                    error_detail=ErrorDetail.BAD_REQUEST,
                )

        # Create an instance and test
        error = CustomTestError(extra_msg="This is a test")
        error_code = error.error_code()

        assert isinstance(error_code, ErrorCode)
        assert error_code.domain == ErrorDomain.BACKENDAI
        assert error_code.operation == ErrorOperation.GENERIC
        assert error_code.error_detail == ErrorDetail.BAD_REQUEST
        assert (
            str(error_code)
            == ErrorDomain.BACKENDAI.value
            + "_"
            + ErrorOperation.GENERIC.value
            + "_"
            + ErrorDetail.BAD_REQUEST.value
        )
