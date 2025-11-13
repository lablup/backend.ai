from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.health.docker import DockerHealthChecker
from ai.backend.common.exception import ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.common.health.exceptions import DockerHealthCheckError


class TestDockerHealthChecker:
    """Test DockerHealthChecker with mocked Docker daemon."""

    @pytest.mark.asyncio
    async def test_success(self) -> None:
        """Test successful health check with mocked Docker daemon."""
        # Mock aiodocker.Docker
        mock_docker = MagicMock()
        mock_docker.version = AsyncMock(return_value={"Version": "24.0.0"})
        mock_docker.close = AsyncMock()

        with patch(
            "ai.backend.agent.health.docker.aiodocker.Docker",
            return_value=mock_docker,
        ):
            checker = DockerHealthChecker(timeout=5.0)
            try:
                # Should not raise
                await checker.check_health()
            finally:
                await checker.close()

        # Verify version was called
        mock_docker.version.assert_called_once()
        # Verify close was called
        mock_docker.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_property(self) -> None:
        """Test that timeout property returns the correct value."""
        mock_docker = MagicMock()
        mock_docker.close = AsyncMock()

        with patch(
            "ai.backend.agent.health.docker.aiodocker.Docker",
            return_value=mock_docker,
        ):
            timeout_value = 3.5
            checker = DockerHealthChecker(timeout=timeout_value)
            try:
                assert checker.timeout == timeout_value
            finally:
                await checker.close()

    @pytest.mark.asyncio
    async def test_docker_connection_failure(self) -> None:
        """Test health check failure when Docker daemon is not accessible."""
        # Mock aiodocker.Docker to raise exception
        mock_docker = MagicMock()
        mock_docker.version = AsyncMock(
            side_effect=ConnectionError("Cannot connect to Docker daemon")
        )
        mock_docker.close = AsyncMock()

        with patch(
            "ai.backend.agent.health.docker.aiodocker.Docker",
            return_value=mock_docker,
        ):
            checker = DockerHealthChecker(timeout=5.0)
            try:
                with pytest.raises(DockerHealthCheckError) as exc_info:
                    await checker.check_health()

                # Should contain error information
                assert "health check failed" in str(exc_info.value).lower()
            finally:
                await checker.close()

    @pytest.mark.asyncio
    async def test_multiple_checks(self) -> None:
        """Test that multiple health checks work correctly."""
        mock_docker = MagicMock()
        mock_docker.version = AsyncMock(return_value={"Version": "24.0.0"})
        mock_docker.close = AsyncMock()

        with patch(
            "ai.backend.agent.health.docker.aiodocker.Docker",
            return_value=mock_docker,
        ):
            checker = DockerHealthChecker(timeout=5.0)
            try:
                # Multiple checks should all succeed
                await checker.check_health()
                await checker.check_health()
                await checker.check_health()
            finally:
                await checker.close()

        # version should have been called 3 times
        assert mock_docker.version.call_count == 3


class TestDockerHealthCheckError:
    """Test DockerHealthCheckError exception attributes."""

    def test_error_attributes(self) -> None:
        """Test that DockerHealthCheckError has correct attributes."""
        error = DockerHealthCheckError("Test error message")

        # Check error attributes
        assert error.error_type == "https://api.backend.ai/probs/docker-health-check-failed"
        assert error.error_title == "Docker health check failed"

        # Check error_code()
        error_code = error.error_code()
        assert error_code.domain == ErrorDomain.HEALTH_CHECK
        assert error_code.operation == ErrorOperation.READ
        assert error_code.error_detail == ErrorDetail.UNAVAILABLE

        # Check HTTP status code (inherited from web.HTTPServiceUnavailable)
        assert error.status_code == 503
