"""Valkey client for the volumes each agent holds."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Final, Self

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.sentinel_monitor.base import AbstractSentinelMonitor
from ai.backend.common.data.storage.types import StorageVolumeDeclaration
from ai.backend.common.exception import BackendAIError
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    BackoffStrategy,
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.types import AgentId, ValkeyTarget
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

valkey_storage_volume_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_STORAGE_VOLUME)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)

_VOLUME_DECLARATIONS_KEY_PREFIX: Final[str] = "storage:volume_declarations"


class ValkeyStorageVolumeClient:
    """
    Client for the volume declarations of each agent.

    The declarations of an agent are a JSON array under a key with the agent id. An empty
    array declares no volume; a missing key, such as one expired, declares nothing known.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
        sentinel_monitor: AbstractSentinelMonitor | None = None,
    ) -> Self:
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            sentinel_monitor=sentinel_monitor,
        )
        await client.connect()
        return cls(client=client)

    @valkey_storage_volume_resilience.apply()
    async def close(self) -> None:
        if self._closed:
            log.debug("valkey storage volume client already closed")
            return
        self._closed = True
        await self._client.disconnect()

    def _make_volume_declarations_key(self, agent_id: AgentId) -> str:
        return f"{_VOLUME_DECLARATIONS_KEY_PREFIX}:{agent_id}"

    @valkey_storage_volume_resilience.apply()
    async def get_volume_declarations(
        self, agent_id: AgentId
    ) -> list[StorageVolumeDeclaration] | None:
        """The volumes declared for the agent, None when the key does not exist."""
        key = self._make_volume_declarations_key(agent_id)
        async with self._client.client() as conn:
            raw_declarations = await conn.get(key)
        if raw_declarations is None:
            return None
        return [
            StorageVolumeDeclaration.model_validate(raw_declaration)
            for raw_declaration in load_json(raw_declarations)
        ]

    @valkey_storage_volume_resilience.apply()
    async def set_volume_declarations(
        self,
        agent_id: AgentId,
        declarations: Sequence[StorageVolumeDeclaration],
        ttl_seconds: int,
    ) -> None:
        """Replaces the volumes declared for the agent; an empty sequence declares no volume."""
        key = self._make_volume_declarations_key(agent_id)
        value = dump_json([declaration.model_dump(mode="json") for declaration in declarations])
        async with self._client.client() as conn:
            await conn.set(key, value, expiry=ExpirySet(ExpiryType.SEC, ttl_seconds))
