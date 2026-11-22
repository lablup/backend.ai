from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from kubernetes_asyncio import client

from ai.backend.common.events.event_types.bgtask.broadcast import BgtaskFailedEvent
from ai.backend.kube.gateway.images import GatewayImages


@pytest.fixture
def core(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    core = AsyncMock()
    monkeypatch.setattr(client, "CoreV1Api", lambda _api: core)
    return core


@pytest.fixture
def producer() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def images(core: AsyncMock, producer: AsyncMock) -> GatewayImages:
    index = MagicMock()
    index.get.return_value = SimpleNamespace(pod_name="s-1-main1", namespace="bai-p")
    return GatewayImages(MagicMock(), index, producer, namespace="bai", port=8080, token="t")


async def _finished_event(producer: AsyncMock) -> object:
    for _ in range(100):
        if producer.broadcast_event_with_cache.await_count:
            break
        await asyncio.sleep(0)
    return producer.broadcast_event_with_cache.await_args.args[1]


class TestImageTask:
    @pytest.mark.parametrize("error", [TimeoutError(), AttributeError("status")])
    async def test_an_unexpected_error_fails_the_task(
        self, images: GatewayImages, core: AsyncMock, producer: AsyncMock, error: Exception
    ) -> None:
        core.read_namespaced_pod.side_effect = error
        task_id = images.commit("k1", "registry/x:1", {})
        event = await _finished_event(producer)
        assert isinstance(event, BgtaskFailedEvent)
        assert str(event.task_id) == task_id
