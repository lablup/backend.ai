from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from zmq.auth.certs import load_certificate

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from ..errors import InvalidManagerKeypairError


@dataclass
class AgentCacheInput:
    """Input required for agent cache setup.

    Contains database and RPC authentication configuration.
    """

    db: ExtendedAsyncSAEngine
    config: ManagerUnifiedConfig


class AgentCacheDependency(NonMonitorableDependencyProvider[AgentCacheInput, AgentRPCCache]):
    """Provides AgentRPCCache lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "agent-cache"

    @asynccontextmanager
    async def provide(self, setup_input: AgentCacheInput) -> AsyncIterator[AgentRPCCache]:
        """Initialize and provide agent RPC cache.

        Args:
            setup_input: Input containing database and config

        Yields:
            Initialized AgentRPCCache
        """
        # Load manager keypair for RPC authentication
        manager_pkey, manager_skey = load_certificate(
            setup_input.config.manager.rpc_auth_manager_keypair
        )
        if manager_skey is None:
            raise InvalidManagerKeypairError("Manager secret key is missing from the keypair file")
        manager_public_key = PublicKey(manager_pkey)
        manager_secret_key = SecretKey(manager_skey)

        # Create agent cache
        agent_cache = AgentRPCCache(setup_input.db, manager_public_key, manager_secret_key)

        yield agent_cache
