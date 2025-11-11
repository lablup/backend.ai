import pytest

from ai.backend.common.exception import (
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
