from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ai.backend.common.types import AgentId
from ai.backend.manager.agent_cache import AgentRPCCache

from .client import AgentClient


@dataclass
class AgentPoolConfig:
    """Configuration for AgentPool"""

    invoke_timeout: Optional[float] = None


class AgentPool:
    """
    Pool for managing agent clients.
    Provides a clean interface for obtaining AgentClient instances.
    """

    _agent_cache: AgentRPCCache
    _config: AgentPoolConfig

    def __init__(
        self, agent_cache: AgentRPCCache, config: Optional[AgentPoolConfig] = None
    ) -> None:
        """
        Initialize the agent pool.

        :param agent_cache: The underlying RPC cache for agent connections
        :param config: Optional configuration for the pool
        """
        self._agent_cache = agent_cache
        self._config = config or AgentPoolConfig()

    def get_agent_client(
        self,
        agent_id: AgentId,
        *,
        invoke_timeout: Optional[float] = None,
        order_key: Optional[str] = None,
    ) -> AgentClient:
        """
        Get an AgentClient for the given agent ID.

        :param agent_id: The ID of the agent to connect to
        :param invoke_timeout: Optional timeout for RPC invocations
        :param order_key: Optional key for ordering RPC calls
        :return: An AgentClient instance for the specified agent
        """
        return AgentClient(
            self._agent_cache,
            agent_id,
            invoke_timeout=invoke_timeout or self._config.invoke_timeout,
            order_key=order_key,
        )
