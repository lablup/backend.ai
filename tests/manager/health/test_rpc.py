from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.exception import ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.common.health_checker import AGENT, ComponentId
from ai.backend.common.types import AgentId
from ai.backend.manager.clients.agent.client import AgentClient
from ai.backend.manager.health.rpc import AgentRpcHealthChecker, RpcHealthCheckError


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

        result = await checker.check_service()

        # Verify health() was called
        mock_health: AsyncMock = mock_agent_client.health  # type: ignore[assignment]
        mock_health.assert_called_once()

        # Verify result
        assert len(result.results) == 1
        component_id = ComponentId(str(mock_agent_client.agent_id))
        assert component_id in result.results
        status = result.results[component_id]
        assert status.is_healthy is True
        assert status.error_message is None
        assert isinstance(status.last_checked_at, datetime)

    @pytest.mark.asyncio
    async def test_target_service_group(
        self,
        mock_agent_client: AgentClient,
    ) -> None:
        """Test that target_service_group returns AGENT."""
        checker = AgentRpcHealthChecker(
            agent_client=mock_agent_client,
            timeout=5.0,
        )

        assert checker.target_service_group == AGENT

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

        result = await checker.check_service()

        # Verify result indicates failure
        assert len(result.results) == 1
        component_id = ComponentId(str(mock_agent_client.agent_id))
        status = result.results[component_id]
        assert status.is_healthy is False
        assert status.error_message is not None
        assert "health check failed" in status.error_message.lower()
        assert isinstance(status.last_checked_at, datetime)

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
        result1 = await checker.check_service()
        result2 = await checker.check_service()
        result3 = await checker.check_service()

        # health() should have been called 3 times
        mock_health: AsyncMock = mock_agent_client.health  # type: ignore[assignment]
        assert mock_health.call_count == 3

        # All results should be healthy
        component_id = ComponentId(str(mock_agent_client.agent_id))
        assert result1.results[component_id].is_healthy
        assert result2.results[component_id].is_healthy
        assert result3.results[component_id].is_healthy

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

        result = await checker.check_service()

        # Verify result indicates failure
        assert len(result.results) == 1
        component_id = ComponentId(str(mock_agent_client.agent_id))
        status = result.results[component_id]
        assert status.is_healthy is False
        assert status.error_message is not None
        assert "health check failed" in status.error_message.lower()
        assert isinstance(status.last_checked_at, datetime)


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
