from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.layered import LayeredIngressState
from ai.backend.appproxy.worker.ingress.redis import RedisIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKey,
    IngressFrontendKind,
    IngressID,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)

FRONTEND_KEY = IngressFrontendKey("10205")
NEGATIVE_TTL = 5.0


@pytest.fixture
def ingress() -> Ingress:
    return Ingress(
        id=IngressID("ingress-10205"),
        authority=IngressAuthority("worker-1"),
        revision=5,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10205),
        ),
        access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
        backend=IngressBackend(
            id=IngressBackendID("backend-1"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


@pytest.fixture
def memory() -> InMemoryIngressState:
    return InMemoryIngressState(negative_ttl=NEGATIVE_TTL)


@pytest.fixture
def redis() -> AsyncMock:
    redis = AsyncMock(spec=RedisIngressState)
    redis.get.return_value = None
    redis.get_all.return_value = []
    return redis


@pytest.fixture
def layered(memory: InMemoryIngressState, redis: AsyncMock) -> LayeredIngressState:
    return LayeredIngressState(memory=memory, redis=redis)


@pytest.fixture
def redis_only(redis: AsyncMock) -> LayeredIngressState:
    return LayeredIngressState(memory=None, redis=redis)


@pytest.fixture
def memory_only(memory: InMemoryIngressState) -> LayeredIngressState:
    return LayeredIngressState(memory=memory, redis=None)


@pytest.fixture
async def ingress_in_memory(memory: InMemoryIngressState, ingress: Ingress) -> None:
    await memory.apply([ingress])


@pytest.fixture
def ingress_in_redis(redis: AsyncMock, ingress: Ingress) -> None:
    redis.get.return_value = ingress
    redis.get_all.return_value = [ingress]


@pytest.fixture
async def key_remembered_missing(memory: InMemoryIngressState) -> None:
    await memory.remember_missing(FRONTEND_KEY)


class TestLayeredIngressState:
    @pytest.mark.usefixtures("ingress_in_memory")
    async def test_get_returns_a_memory_hit_without_reading_redis(
        self, layered: LayeredIngressState, redis: AsyncMock, ingress: Ingress
    ) -> None:
        assert await layered.get(FRONTEND_KEY) == ingress
        redis.get.assert_not_awaited()

    @pytest.mark.usefixtures("ingress_in_redis")
    async def test_get_fills_memory_with_a_redis_hit(
        self, layered: LayeredIngressState, memory: InMemoryIngressState, ingress: Ingress
    ) -> None:
        assert await layered.get(FRONTEND_KEY) == ingress
        assert await memory.get(FRONTEND_KEY) == ingress

    async def test_get_returns_none_when_every_layer_misses(
        self, layered: LayeredIngressState
    ) -> None:
        assert await layered.get(FRONTEND_KEY) is None

    async def test_miss_in_every_layer_skips_redis_on_the_next_get(
        self, layered: LayeredIngressState, redis: AsyncMock
    ) -> None:
        await layered.get(FRONTEND_KEY)
        with pytest.raises(IngressNotFoundError):
            await layered.get(FRONTEND_KEY)
        redis.get.assert_awaited_once_with(FRONTEND_KEY)

    @pytest.mark.usefixtures("key_remembered_missing")
    async def test_key_known_missing_raises_without_reading_redis(
        self, layered: LayeredIngressState, redis: AsyncMock
    ) -> None:
        with pytest.raises(IngressNotFoundError):
            await layered.get(FRONTEND_KEY)
        redis.get.assert_not_awaited()

    async def test_miss_without_a_memory_layer_reads_as_none(
        self, redis_only: LayeredIngressState
    ) -> None:
        assert await redis_only.get(FRONTEND_KEY) is None

    async def test_miss_without_a_redis_layer_reads_as_none(
        self, memory_only: LayeredIngressState
    ) -> None:
        assert await memory_only.get(FRONTEND_KEY) is None

    @pytest.mark.usefixtures("ingress_in_redis")
    async def test_get_all_returns_the_last_layers_set(
        self, layered: LayeredIngressState, ingress: Ingress
    ) -> None:
        assert await layered.get_all() == [ingress]
