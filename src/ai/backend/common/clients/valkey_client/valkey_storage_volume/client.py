"""Valkey client for the volumes each agent holds."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Final, Self, cast

from glide import Batch, ExpirySet, ExpiryType

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
        self, agent_ids: Sequence[AgentId]
    ) -> dict[AgentId, list[StorageVolumeDeclaration] | None]:
        """The volumes declared for each agent, None for an agent whose key does not exist."""
        if not agent_ids:
            return {}
        keys = [self._make_volume_declarations_key(agent_id) for agent_id in agent_ids]
        async with self._client.client() as conn:
            raw_values = await conn.mget(cast(list[str | bytes], keys))
        return {
            agent_id: self._parse_volume_declarations(raw_declarations)
            for agent_id, raw_declarations in zip(agent_ids, raw_values, strict=True)
        }

    @valkey_storage_volume_resilience.apply()
    async def set_volume_declarations(
        self,
        declarations: Mapping[AgentId, Sequence[StorageVolumeDeclaration]],
        ttl_seconds: int,
    ) -> None:
        """Replaces the volumes declared for each agent at once; an empty sequence declares
        no volume."""
        if not declarations:
            return
        batch = Batch(is_atomic=True)
        for agent_id, agent_declarations in declarations.items():
            batch.set(
                self._make_volume_declarations_key(agent_id),
                dump_json([
                    declaration.model_dump(mode="json") for declaration in agent_declarations
                ]),
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )
        async with self._client.client() as conn:
            await conn.exec(batch, raise_on_error=True)

    def _parse_volume_declarations(
        self, raw_declarations: bytes | None
    ) -> list[StorageVolumeDeclaration] | None:
        if raw_declarations is None:
            return None
        return [
            StorageVolumeDeclaration.model_validate(raw_declaration)
            for raw_declaration in load_json(raw_declarations)
        ]
