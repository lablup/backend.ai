from __future__ import annotations

from datetime import datetime, timezone

from aiohttp import web

from ai.backend.common.exception import ErrorCode, ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.common.health_checker.abc import StaticServiceHealthChecker
from ai.backend.common.health_checker.exceptions import HealthCheckError
from ai.backend.common.health_checker.types import (
    AGENT,
    ComponentHealthStatus,
    ComponentId,
    ServiceGroup,
    ServiceHealth,
)
from ai.backend.manager.clients.agent.client import AgentClient


class RpcHealthCheckError(HealthCheckError, web.HTTPServiceUnavailable):
    """Raised when RPC health check fails."""

    error_type = "https://api.backend.ai/probs/rpc-health-check-failed"
    error_title = "RPC health check failed"

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.HEALTH_CHECK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class AgentRpcHealthChecker(StaticServiceHealthChecker):
    """
    Health checker for Agent RPC connections.

    Checks if the agent RPC endpoint is reachable and responsive.
    """

    _agent_client: AgentClient
    _timeout: float

    def __init__(self, agent_client: AgentClient, timeout: float = 5.0) -> None:
        """
        Initialize AgentRpcHealthChecker.

        Args:
            agent_client: The agent RPC client instance to check
            timeout: Timeout in seconds for the health check
        """
        self._agent_client = agent_client
        self._timeout = timeout

    @property
    def target_service_group(self) -> ServiceGroup:
        """The service group this checker monitors."""
        return AGENT

    async def check_service(self) -> ServiceHealth:
        """
        Check agent RPC health by calling the health RPC method.

        Verifies connectivity by making a lightweight RPC call to the agent.

        Returns:
            ServiceHealth containing status for the agent RPC connection
        """
        check_time = datetime.now(timezone.utc)
        component_id = ComponentId(str(self._agent_client.agent_id))

        try:
            await self._agent_client.health()
            status = ComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        except Exception as e:
            status = ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message=f"Agent RPC health check failed: {e}",
            )

        return ServiceHealth(results={component_id: status})

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
