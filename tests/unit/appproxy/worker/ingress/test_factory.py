from __future__ import annotations

from unittest.mock import Mock

import pytest

from ai.backend.appproxy.worker.config import IngressConfig
from ai.backend.appproxy.worker.ingress.factory import IngressState, IngressStateFactory
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.redis import RedisIngressState
from ai.backend.appproxy.worker.ingress.validating import ValidatingIngressWriter
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority


@pytest.fixture
def valkey_client() -> ValkeyLiveClient:
    return Mock(spec=ValkeyLiveClient)


def _create(delivery_mode: str, layers: list[str], valkey_client: ValkeyLiveClient) -> IngressState:
    config = IngressConfig.model_validate({"delivery_mode": delivery_mode, "layers": layers})
    return IngressStateFactory(config, IngressAuthority("worker-1"), valkey_client).create()


class TestIngressStateFactory:
    def test_in_memory_only_writes_through_validation(
        self, valkey_client: ValkeyLiveClient
    ) -> None:
        state = _create("api", ["in-memory"], valkey_client)
        [in_memory] = state.reader.layers
        assert isinstance(in_memory, InMemoryIngressState)
        assert isinstance(state.writer, ValidatingIngressWriter)

    def test_in_memory_and_redis_read_in_order(self, valkey_client: ValkeyLiveClient) -> None:
        state = _create("redis", ["in-memory", "redis"], valkey_client)
        in_memory, redis = state.reader.layers
        assert isinstance(in_memory, InMemoryIngressState)
        assert isinstance(redis, RedisIngressState)
        assert isinstance(state.writer, ValidatingIngressWriter)

    def test_redis_only_has_no_writer(self, valkey_client: ValkeyLiveClient) -> None:
        state = _create("redis", ["redis"], valkey_client)
        assert [type(layer) for layer in state.reader.layers] == [RedisIngressState]
        assert state.writer is None
