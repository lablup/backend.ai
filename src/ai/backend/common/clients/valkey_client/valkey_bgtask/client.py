from __future__ import annotations

import json
import logging
from typing import Optional, Self, Set
from collections.abc import Sequence,Iterable

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.common.defs import REDIS_BGTASK_DB
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_bgtask client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_BGTASK)


class ValkeyBgtaskClient:
    """
    Client for background task management operations using Valkey/Glide.
    Provides task-specific methods instead of generic Redis operations.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int = REDIS_BGTASK_DB,
        human_readable_name: str = "bgtask",
    ) -> Self:
        """
        Create a ValkeyBgtaskClient instance.

        :param valkey_target: The target Valkey server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name for the client.
        """
        client = create_valkey_client(
            valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client)

    async def close(self) -> None:
        """Close the client connection."""
        if not self._closed:
            await self._client.disconnect()
            self._closed = True

    # Task metadata operations
    @valkey_decorator()
    async def save_task(self, key: str, value: str, ttl_seconds: int) -> None:
        """Save task metadata with TTL"""
        await self._client.client.set(
            key,
            value,
            expiry=ExpirySet(ExpiryType.SEC, ttl_seconds)
        )

    @valkey_decorator()
    async def get_task(self, key: str) -> Optional[str]:
        """Get task metadata"""
        result = await self._client.client.get(key)
        if result:
            return result.decode() if isinstance(result, bytes) else result
        return None
    
    @valkey_decorator()
    async def get_tasks(self, keys: Sequence[str]) -> dict[str, str]:
        """Get multiple task metadata"""
        results = await self._client.client.mget(list(keys))
        return {
            key: (result.decode() if isinstance(result, bytes) else result)
            for key, result in zip(keys, results) if result is not None
        }

    @valkey_decorator()
    async def delete_task(self, keys: list[str]) -> None:
        """Delete task metadata"""
        if keys:
            await self._client.client.delete(keys)

    # Set operations for task tracking
    @valkey_decorator()
    async def add_to_set(self, key: str, members: list[str]) -> None:
        """Add members to a set"""
        if members:
            await self._client.client.sadd(key, members)

    @valkey_decorator()
    async def remove_from_set(self, key: str, members: list[str]) -> None:
        """Remove members from a set"""
        if members:
            await self._client.client.srem(key, members)

    @valkey_decorator()
    async def get_set_members(self, key: str) -> Set[str]:
        """Get all members of a set"""
        result = await self._client.client.smembers(key)
        if not result:
            return set()
        
        return {
            member.decode() if isinstance(member, bytes) else member
            for member in result
        }

    # TTL operations
    @valkey_decorator()
    async def set_ttl(self, key: str, ttl_seconds: int) -> None:
        """Set or refresh TTL for a key"""
        await self._client.client.expire(key, ttl_seconds)

    @valkey_decorator()
    async def set_heartbeats(self, keys: Sequence[str], value: float, ttl_seconds: int) -> None:
        """Set heartbeat data with TTL"""
        await self._client.client.mset(
            {key: str(value) for key in keys},
        )
        for key in keys:
            await self._client.client.expire(key, ttl_seconds)

    @valkey_decorator()
    async def get_heartbeats(self, key: Sequence[str]) -> list[float]:
        """Get heartbeat data"""
        result = await self._client.client.mget(list(key))
        return [
            float(value.decode())
            for value in result if value is not None
        ]
