from __future__ import annotations

from dataclasses import dataclass

from ai.backend.appproxy.common.types import IngressUpdateMode
from ai.backend.appproxy.worker.config import IngressConfig, IngressLayerType
from ai.backend.appproxy.worker.ingress.abc import IngressReader
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.layered import LayeredIngressState
from ai.backend.appproxy.worker.ingress.redis import RedisIngressState
from ai.backend.appproxy.worker.ingress.validating import ValidatingIngressWriter
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority, IngressRedisKey
from ai.backend.common.exception import InvalidConfigError


@dataclass(frozen=True)
class IngressState:
    reader: LayeredIngressState
    writer: ValidatingIngressWriter | None
    """None when the worker holds no in-memory layer."""
    mode: IngressUpdateMode


class IngressStateFactory:
    _config: IngressConfig
    _authority: IngressAuthority
    _valkey_client: ValkeyLiveClient

    def __init__(
        self, config: IngressConfig, authority: IngressAuthority, valkey_client: ValkeyLiveClient
    ) -> None:
        self._config = config
        self._authority = authority
        self._valkey_client = valkey_client

    def create(self) -> IngressState:
        readers: list[IngressReader] = []
        in_memory: InMemoryIngressState | None = None
        writer: ValidatingIngressWriter | None = None
        for layer_type in self._config.layers:
            match layer_type:
                case IngressLayerType.IN_MEMORY:
                    in_memory = self._in_memory()
                    readers.append(in_memory)
                    writer = ValidatingIngressWriter(in_memory, self._authority)
                case IngressLayerType.REDIS:
                    readers.append(self._redis())
        if not readers:
            raise InvalidConfigError("No ingress layer is configured")
        return IngressState(
            reader=LayeredIngressState(readers, in_memory=in_memory),
            writer=writer,
            mode=self._config.mode,
        )

    def _in_memory(self) -> InMemoryIngressState:
        return InMemoryIngressState(
            ttl=self._config.in_memory.ttl,
            negative_ttl=self._config.in_memory.negative_ttl,
        )

    def _redis(self) -> RedisIngressState:
        return RedisIngressState(
            self._authority, IngressRedisKey(self._config.redis.key_prefix), self._valkey_client
        )
