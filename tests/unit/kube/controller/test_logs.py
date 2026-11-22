from __future__ import annotations

from typing import override
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.log.types import ContainerLogData
from ai.backend.common.types import KernelId
from ai.backend.kube.controller.logs import KernelLogSync

KERNEL_ID = KernelId(UUID("11111111-0000-0000-0000-000000000001"))


class FakeLogStore(ValkeyContainerLogClient):
    """Container log chunks as the Valkey list holds them."""

    chunks: dict[str, list[ContainerLogData]]

    def __init__(self) -> None:
        self.chunks = {}

    @override
    async def enqueue_container_logs(self, container_id: str, logs: ContainerLogData) -> None:
        self.chunks.setdefault(container_id, []).append(logs)

    @override
    async def clear_container_logs(self, container_id: str) -> None:
        self.chunks.pop(container_id, None)


@pytest.fixture
def core(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    core = AsyncMock()
    core.read_namespaced_pod_log.return_value = "hello\n"
    monkeypatch.setattr(client, "CoreV1Api", lambda _api: core)
    return core


@pytest.fixture
def store() -> FakeLogStore:
    return FakeLogStore()


@pytest.fixture
def producer() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sync(core: AsyncMock, store: FakeLogStore, producer: AsyncMock) -> KernelLogSync:
    return KernelLogSync(MagicMock(), store, producer)


class TestKernelLogSync:
    async def test_a_repeated_hand_off_replaces_the_chunks(
        self, sync: KernelLogSync, store: FakeLogStore, producer: AsyncMock
    ) -> None:
        await sync.sync("bai-p", "s-1-main1", KERNEL_ID, "cid")
        await sync.sync("bai-p", "s-1-main1", KERNEL_ID, "cid")
        assert len(store.chunks["cid"]) == 1
        assert producer.anycast_event.await_count == 2

    async def test_the_log_read_has_a_timeout(self, sync: KernelLogSync, core: AsyncMock) -> None:
        await sync.sync("bai-p", "s-1-main1", KERNEL_ID, "cid")
        assert core.read_namespaced_pod_log.call_args.kwargs["_request_timeout"] > 0

    async def test_a_pod_gone_sends_nothing(
        self, sync: KernelLogSync, core: AsyncMock, store: FakeLogStore, producer: AsyncMock
    ) -> None:
        core.read_namespaced_pod_log.side_effect = ApiException(status=404)
        await sync.sync("bai-p", "s-1-main1", KERNEL_ID, "cid")
        assert store.chunks == {}
        producer.anycast_event.assert_not_called()

    async def test_a_server_error_is_retried_by_the_caller(
        self, sync: KernelLogSync, core: AsyncMock
    ) -> None:
        core.read_namespaced_pod_log.side_effect = ApiException(status=503)
        with pytest.raises(ApiException):
            await sync.sync("bai-p", "s-1-main1", KERNEL_ID, "cid")
