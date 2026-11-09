from __future__ import annotations

from typing import override

from ai.backend.appproxy.worker.ingress.abc import IngressReader
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
    IngressFrontendKey,
    IngressRedisKey,
)


class RedisIngressState(IngressReader):
    """Ingresses of one authority read from the site Redis."""

    _authority: IngressAuthority
    _key: IngressRedisKey
    _client: ValkeyLiveClient

    def __init__(
        self, authority: IngressAuthority, key: IngressRedisKey, client: ValkeyLiveClient
    ) -> None:
        self._authority = authority
        self._key = key
        self._client = client

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        value = await self._client.get_live_data(self._key.of(self._authority, frontend_key))
        if value is None:
            return None
        return Ingress.model_validate_json(value)

    @override
    async def get_all(self) -> list[Ingress]:
        redis_keys = await self._client.scan_keys(self._key.pattern(self._authority))
        values = await self._client.get_multiple_live_data(redis_keys)
        # A key deleted between the scan and the read comes back as None.
        return [Ingress.model_validate_json(value) for value in values if value is not None]
