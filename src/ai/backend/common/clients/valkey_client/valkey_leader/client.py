"""Valkey-based leader election client."""

from __future__ import annotations

import logging
from typing import Final, Self

from glide import Script

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_leader client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_STREAM)

# Lua script for atomic leader election/renewal
LEADER_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if not current then
    redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
    return 1
elseif current == ARGV[1] then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
    return 1
else
    return 0
end
"""

# Lua script for atomic leader release
RELEASE_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if current == ARGV[1] then
    redis.call('DEL', KEYS[1])
    return 1
else
    return 0
end
"""


class ValkeyLeaderClient:
    """
    Client for leader election using Valkey/Redis with GlideClient.

    Provides stateless leader election operations.
    """

    _client: AbstractValkeyClient
    _leader_script: Script
    _release_script: Script

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
        """
        Initialize the Valkey leader client.

        Args:
            client: Abstract Valkey client
        """
        self._client = client
        # Create script objects (will be registered when used)
        self._leader_script = Script(LEADER_SCRIPT)
        self._release_script = Script(RELEASE_SCRIPT)

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
    ) -> Self:
        """
        Create a ValkeyLeaderClient instance.

        Args:
            valkey_target: The target Valkey server to connect to
            db_id: The database index to use
            human_readable_name: Human-readable name for logging

        Returns:
            An instance of ValkeyLeaderClient
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_decorator()
    async def close(self) -> None:
        """Close the ValkeyLeaderClient connection."""
        await self._client.disconnect()

    @valkey_decorator(retry_count=1)
    async def acquire_or_renew_leadership(
        self,
        server_id: str,
        leader_key: str,
        lease_duration: int,
    ) -> bool:
        """
        Try to acquire or renew leadership for a server.

        This is a stateless operation that returns whether the server
        successfully acquired or renewed leadership.

        Args:
            server_id: Unique identifier for the server
            leader_key: Redis key for leader election
            lease_duration: Leader lease duration in seconds

        Returns:
            True if the server acquired or renewed leadership, False otherwise

        Raises:
            Exception: Any exception from the underlying Redis operation
        """
        # Execute the Lua script
        result = await self._client.client.invoke_script(
            script=self._leader_script,
            keys=[leader_key],
            args=[server_id, str(lease_duration)],
        )
        return bool(result == 1)

    @valkey_decorator()
    async def release_leadership(
        self,
        server_id: str,
        leader_key: str,
    ) -> bool:
        """
        Release leadership if held by the specified server.

        This is an atomic operation that only releases leadership if
        the specified server is the current leader.

        Args:
            server_id: Unique identifier for the server
            leader_key: Redis key for leader election

        Returns:
            True if leadership was released, False if not held

        Raises:
            Exception: Any exception from the underlying Redis operation
        """
        # Execute the Lua script for atomic release
        result = await self._client.client.invoke_script(
            script=self._release_script,
            keys=[leader_key],
            args=[server_id],
        )
        released = bool(result == 1)
        if released:
            log.info(f"Server {server_id} released leadership for {leader_key}")
        return released
