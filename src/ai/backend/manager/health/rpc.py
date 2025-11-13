from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import ErrorCode, ErrorDetail, ErrorDomain, ErrorOperation
from ai.backend.common.health.abc import HealthChecker
from ai.backend.common.health.exceptions import HealthCheckError
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


class AgentRpcHealthChecker(HealthChecker):
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

    async def check_health(self) -> None:
        """
        Check agent RPC health by calling the health RPC method.

        Verifies connectivity by making a lightweight RPC call to the agent.

        Raises:
            RpcHealthCheckError: If the RPC call fails
        """
        try:
            await self._agent_client.health()
        except Exception as e:
            raise RpcHealthCheckError(
                f"Agent RPC health check failed for {self._agent_client.agent_id}: {e}"
            ) from e

    @property
    def timeout(self) -> float:
        """The timeout for the health check in seconds."""
        return self._timeout
