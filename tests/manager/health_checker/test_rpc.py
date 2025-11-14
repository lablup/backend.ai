from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.exception import ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.common.types import AgentId
from ai.backend.manager.clients.agent.client import AgentClient
from ai.backend.manager.health_checker.rpc import AgentRpcHealthChecker, RpcHealthCheckError


class TestAgentRpcHealthChecker:
    """Test AgentRpcHealthChecker with mocked agent clients."""

    @pytest.fixture
    def mock_agent_client(self) -> AgentClient:
        """
        Mock AgentClient for RPC testing.

        By default, health() succeeds and returns a valid HealthCheckResponse.
        """
        client = AsyncMock(spec=AgentClient)
        client.agent_id = AgentId("test-agent-id")

        # Default: health() succeeds
        default_response: Mapping[str, Any] = {
            "overall_healthy": True,
            "connectivity_checks": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        client.health = AsyncMock(return_value=default_response)

        return client

    @pytest.mark.asyncio
    async def test_success(self, mock_agent_client: AgentClient) -> None:
        """Test successful health check with mock agent client."""
        checker = AgentRpcHealthChecker(
            agent_client=mock_agent_client,
            timeout=5.0,
        )

        # Should not raise
        await checker.check_health()

        # Verify health() was called
        mock_health: AsyncMock = mock_agent_client.health  # type: ignore[assignment]
        mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_property(
        self,
        mock_agent_client: AgentClient,
    ) -> None:
        """Test that timeout property returns the correct value."""
        timeout_value = 3.5
        checker = AgentRpcHealthChecker(
            agent_client=mock_agent_client,
            timeout=timeout_value,
        )

        assert checker.timeout == timeout_value

    @pytest.mark.asyncio
    async def test_rpc_failure(self, mock_agent_client: AgentClient) -> None:
        """Test health check failure when RPC call raises exception."""
        # Configure mock to raise exception
        mock_health = AsyncMock(side_effect=RuntimeError("RPC connection failed"))
        mock_agent_client.health = mock_health  # type: ignore[method-assign]

        checker = AgentRpcHealthChecker(
            agent_client=mock_agent_client,
            timeout=5.0,
        )

        with pytest.raises(RpcHealthCheckError) as exc_info:
            await checker.check_health()

        # Error message should include agent_id
        assert str(mock_agent_client.agent_id) in str(exc_info.value)
        assert "health check failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_multiple_checks(
        self,
        mock_agent_client: AgentClient,
    ) -> None:
        """Test that multiple health checks work correctly."""
        checker = AgentRpcHealthChecker(
            agent_client=mock_agent_client,
            timeout=5.0,
        )

        # Multiple checks should all succeed
        await checker.check_health()
        await checker.check_health()
        await checker.check_health()

        # health() should have been called 3 times
        mock_health: AsyncMock = mock_agent_client.health  # type: ignore[assignment]
        assert mock_health.call_count == 3

    @pytest.mark.asyncio
    async def test_connection_timeout(self, mock_agent_client: AgentClient) -> None:
        """Test health check failure when RPC call times out."""
        # Configure mock to simulate timeout
        mock_health = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_agent_client.health = mock_health  # type: ignore[method-assign]

        checker = AgentRpcHealthChecker(
            agent_client=mock_agent_client,
            timeout=5.0,
        )

        with pytest.raises(RpcHealthCheckError) as exc_info:
            await checker.check_health()

        # Error message should indicate the issue
        error_msg = str(exc_info.value).lower()
        assert "health check failed" in error_msg
        assert str(mock_agent_client.agent_id) in str(exc_info.value)


class TestRpcHealthCheckError:
    """Test RpcHealthCheckError exception attributes."""

    def test_error_attributes(self) -> None:
        """Test that RpcHealthCheckError has correct attributes."""
        error = RpcHealthCheckError("Test error message")

        # Check error attributes
        assert error.error_type == "https://api.backend.ai/probs/rpc-health-check-failed"
        assert error.error_title == "RPC health check failed"

        # Check error_code()
        error_code = error.error_code()
        assert error_code.domain == ErrorDomain.HEALTH_CHECK
        assert error_code.operation == ErrorOperation.READ
        assert error_code.error_detail == ErrorDetail.UNAVAILABLE

        # Check HTTP status code (inherited from web.HTTPServiceUnavailable)
        assert error.status_code == 503
