from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from unittest.mock import AsyncMock

import pytest

from ai.backend.appproxy.worker.errors.ingress import IngressNotRegisteredError
from ai.backend.appproxy.worker.ingress.abc import IngressReader
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
    IngressKey,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)

AUTHORITY = IngressAuthority("worker-1")
FRONTEND_KEY = IngressFrontendKey("port-10205")
ANOTHER_FRONTEND_KEY = IngressFrontendKey("port-10206")
NEGATIVE_TTL = 5.0


@dataclass(frozen=True)
class _LayersCase:
    layers: list[str]


@dataclass(frozen=True)
class _InvalidationDuringRedisReadCase:
    invalidated_key: IngressFrontendKey
    expected_held_keys: list[IngressFrontendKey]


@dataclass(frozen=True)
class _LayeredWithTheRedisReadHeldOpen:
    layered: LayeredIngressState
    memory: InMemoryIngressState
    redis: AsyncMock
    redis_read_started: asyncio.Event
    release_redis_read: asyncio.Event


class _MemoryStateBeforeInvalidation(StrEnum):
    HOLDING_A_STALE_REVISION = "holding-a-stale-revision"
    REMEMBERING_THE_KEY_MISSING = "remembering-the-key-missing"


@pytest.fixture
def ingress() -> Ingress:
    return Ingress(
        id=IngressID("ingress-10205"),
        authority=AUTHORITY,
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
    return LayeredIngressState([memory, redis], in_memory=memory)


@pytest.fixture
def configured_layered(
    request: pytest.FixtureRequest, memory: InMemoryIngressState, redis: AsyncMock
) -> LayeredIngressState:
    layers_by_name: dict[str, IngressReader] = {"in-memory": memory, "redis": redis}
    case: _LayersCase = request.param
    return LayeredIngressState(
        [layers_by_name[name] for name in case.layers],
        in_memory=memory if "in-memory" in case.layers else None,
    )


@pytest.fixture
async def ingress_in_memory(memory: InMemoryIngressState, ingress: Ingress) -> None:
    await memory.apply([ingress])


@pytest.fixture
def ingress_in_redis(redis: AsyncMock, ingress: Ingress) -> None:
    redis.get.return_value = ingress
    redis.get_all.return_value = [ingress]


@pytest.fixture
async def key_removed(memory: InMemoryIngressState, ingress: Ingress) -> None:
    await memory.apply([ingress])
    await memory.remove([IngressKey(authority=AUTHORITY, frontend_key=FRONTEND_KEY)])


@pytest.fixture
async def layered_with_redis_holding_a_newer_ingress_than_memory(
    request: pytest.FixtureRequest,
    layered: LayeredIngressState,
    memory: InMemoryIngressState,
    redis: AsyncMock,
    ingress: Ingress,
) -> LayeredIngressState:
    memory_state: _MemoryStateBeforeInvalidation = request.param
    match memory_state:
        case _MemoryStateBeforeInvalidation.HOLDING_A_STALE_REVISION:
            await memory.apply([ingress.model_copy(update={"revision": ingress.revision - 1})])
        case _MemoryStateBeforeInvalidation.REMEMBERING_THE_KEY_MISSING:
            await memory.apply([ingress])
            await memory.remove([IngressKey(authority=AUTHORITY, frontend_key=FRONTEND_KEY)])
    redis.get.return_value = ingress
    return layered


@pytest.fixture
def layered_with_the_redis_read_held_open(
    layered: LayeredIngressState,
    memory: InMemoryIngressState,
    redis: AsyncMock,
    ingress: Ingress,
) -> _LayeredWithTheRedisReadHeldOpen:
    redis_read_started = asyncio.Event()
    release_redis_read = asyncio.Event()

    async def read_redis_once_released(frontend_key: IngressFrontendKey) -> Ingress:
        redis_read_started.set()
        await release_redis_read.wait()
        return ingress

    redis.get.side_effect = read_redis_once_released
    return _LayeredWithTheRedisReadHeldOpen(
        layered=layered,
        memory=memory,
        redis=redis,
        redis_read_started=redis_read_started,
        release_redis_read=release_redis_read,
    )


class TestLayeredIngressState:
    @pytest.mark.usefixtures("ingress_in_memory")
    async def test_get_returns_a_memory_hit_without_reading_redis(
        self, layered: LayeredIngressState, redis: AsyncMock, ingress: Ingress
    ) -> None:
        assert await layered.get(FRONTEND_KEY) == ingress
        redis.get.assert_not_awaited()

    @pytest.mark.parametrize(
        "configured_layered",
        [
            _LayersCase(layers=["in-memory", "redis"]),
            _LayersCase(layers=["redis", "in-memory"]),
        ],
        ids=lambda case: "+".join(case.layers),
        indirect=True,
    )
    @pytest.mark.usefixtures("ingress_in_redis")
    async def test_get_writes_a_redis_hit_to_memory(
        self,
        configured_layered: LayeredIngressState,
        memory: InMemoryIngressState,
        ingress: Ingress,
    ) -> None:
        assert await configured_layered.get(FRONTEND_KEY) == ingress
        assert await memory.get(FRONTEND_KEY) == ingress

    @pytest.mark.parametrize(
        "configured_layered",
        [
            _LayersCase(layers=["in-memory"]),
            _LayersCase(layers=["redis"]),
            _LayersCase(layers=["in-memory", "redis"]),
        ],
        ids=lambda case: "+".join(case.layers),
        indirect=True,
    )
    async def test_key_no_layer_holds_raises_not_registered(
        self, configured_layered: LayeredIngressState
    ) -> None:
        with pytest.raises(IngressNotRegisteredError):
            await configured_layered.get(FRONTEND_KEY)

    async def test_key_no_layer_holds_is_read_from_redis_again(
        self, layered: LayeredIngressState, redis: AsyncMock
    ) -> None:
        for _ in range(2):
            with pytest.raises(IngressNotRegisteredError):
                await layered.get(FRONTEND_KEY)
        assert redis.get.await_count == 2

    @pytest.mark.usefixtures("key_removed")
    async def test_key_removed_within_negative_ttl_reads_as_none_without_reading_redis(
        self, layered: LayeredIngressState, redis: AsyncMock
    ) -> None:
        assert await layered.get(FRONTEND_KEY) is None
        redis.get.assert_not_awaited()

    @pytest.mark.usefixtures("ingress_in_redis")
    async def test_get_all_returns_the_last_layers_set(
        self, layered: LayeredIngressState, ingress: Ingress
    ) -> None:
        assert await layered.get_all() == [ingress]

    @pytest.mark.parametrize(
        "layered_with_redis_holding_a_newer_ingress_than_memory",
        list(_MemoryStateBeforeInvalidation),
        ids=lambda memory_state: memory_state.value,
        indirect=True,
    )
    async def test_invalidated_key_is_read_from_redis_again(
        self,
        layered_with_redis_holding_a_newer_ingress_than_memory: LayeredIngressState,
        memory: InMemoryIngressState,
        ingress: Ingress,
    ) -> None:
        layered = layered_with_redis_holding_a_newer_ingress_than_memory
        await memory.invalidate([FRONTEND_KEY])

        assert await layered.get(FRONTEND_KEY) == ingress

    @pytest.mark.parametrize(
        "case",
        [
            _InvalidationDuringRedisReadCase(invalidated_key=FRONTEND_KEY, expected_held_keys=[]),
            _InvalidationDuringRedisReadCase(
                invalidated_key=ANOTHER_FRONTEND_KEY, expected_held_keys=[FRONTEND_KEY]
            ),
        ],
        ids=lambda case: case.invalidated_key,
    )
    async def test_redis_hit_stays_in_memory_unless_its_key_is_invalidated_during_the_read(
        self,
        case: _InvalidationDuringRedisReadCase,
        layered_with_the_redis_read_held_open: _LayeredWithTheRedisReadHeldOpen,
    ) -> None:
        situation = layered_with_the_redis_read_held_open
        read = asyncio.create_task(situation.layered.get(FRONTEND_KEY))
        await situation.redis_read_started.wait()
        invalidation = asyncio.create_task(situation.memory.invalidate([case.invalidated_key]))
        await asyncio.sleep(0)
        situation.release_redis_read.set()
        await asyncio.gather(read, invalidation)

        held_ingresses = await situation.memory.get_all()
        assert [
            held_ingress.frontend.key() for held_ingress in held_ingresses
        ] == case.expected_held_keys

    async def test_concurrent_reads_of_a_key_missing_in_memory_read_redis_once(
        self, layered_with_the_redis_read_held_open: _LayeredWithTheRedisReadHeldOpen
    ) -> None:
        situation = layered_with_the_redis_read_held_open
        reads = [asyncio.create_task(situation.layered.get(FRONTEND_KEY)) for _ in range(2)]
        await situation.redis_read_started.wait()
        situation.release_redis_read.set()
        await asyncio.gather(*reads)

        assert situation.redis.get.await_count == 1
