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
from ai.backend.common.exception import GenericNotImplementedError


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
        # Read IngressRedisKey.of(authority, key) and validate it as Ingress.
        raise GenericNotImplementedError

    @override
    async def get_all(self) -> list[Ingress]:
        # Scan IngressRedisKey.pattern(authority) and validate each value.
        raise GenericNotImplementedError
