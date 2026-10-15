from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.appproxy.worker.ingress.redis import RedisIngressState
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
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
    IngressRedisKey,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)

AUTHORITY = IngressAuthority("worker-1")
FRONTEND_KEY = IngressFrontendKey("10205")
KEY_PREFIX = "appproxy:ingress"


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
def valkey_client() -> AsyncMock:
    client = AsyncMock(spec=ValkeyLiveClient)
    client.get_live_data.return_value = None
    client.scan_keys.return_value = []
    client.get_multiple_live_data.return_value = []
    return client


@pytest.fixture
def state(valkey_client: AsyncMock) -> RedisIngressState:
    return RedisIngressState(AUTHORITY, IngressRedisKey(KEY_PREFIX), valkey_client)


@pytest.fixture
def ingress_in_redis(valkey_client: AsyncMock, ingress: Ingress) -> None:
    valkey_client.get_live_data.return_value = ingress.model_dump_json().encode()


@pytest.fixture
def one_of_two_scanned_keys_deleted_before_read(valkey_client: AsyncMock, ingress: Ingress) -> None:
    valkey_client.scan_keys.return_value = [
        f"{KEY_PREFIX}:{AUTHORITY}:10205",
        f"{KEY_PREFIX}:{AUTHORITY}:10206",
    ]
    valkey_client.get_multiple_live_data.return_value = [ingress.model_dump_json().encode(), None]


class TestRedisIngressState:
    @pytest.mark.usefixtures("ingress_in_redis")
    async def test_get_reads_the_authority_key(
        self, state: RedisIngressState, valkey_client: AsyncMock, ingress: Ingress
    ) -> None:
        assert await state.get(FRONTEND_KEY) == ingress
        valkey_client.get_live_data.assert_awaited_once_with(f"{KEY_PREFIX}:{AUTHORITY}:10205")

    async def test_get_returns_none_for_a_key_redis_does_not_hold(
        self, state: RedisIngressState
    ) -> None:
        assert await state.get(FRONTEND_KEY) is None

    @pytest.mark.usefixtures("one_of_two_scanned_keys_deleted_before_read")
    async def test_get_all_reads_every_key_of_the_authority_still_held(
        self, state: RedisIngressState, valkey_client: AsyncMock, ingress: Ingress
    ) -> None:
        assert await state.get_all() == [ingress]
        valkey_client.scan_keys.assert_awaited_once_with(f"{KEY_PREFIX}:{AUTHORITY}:*")
