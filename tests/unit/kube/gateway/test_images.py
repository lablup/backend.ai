from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from kubernetes_asyncio import client

from ai.backend.common.events.event_types.bgtask.broadcast import (
    BgtaskCancelledEvent,
    BgtaskFailedEvent,
)
from ai.backend.kube.gateway.images import ANNOTATION_COMMITTED_IMAGE, GatewayImages, newest_commit


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

    async def test_closing_cancels_a_running_task_and_reports_it(
        self, images: GatewayImages, core: AsyncMock, producer: AsyncMock
    ) -> None:
        started = asyncio.Event()

        async def hang(*_args: Any) -> None:
            started.set()
            await asyncio.Event().wait()

        core.read_namespaced_pod.side_effect = hang
        task_id = images.commit("k1", "registry/x:1", {})
        await started.wait()
        await images.close()
        event = producer.broadcast_event_with_cache.await_args.args[1]
        assert isinstance(event, BgtaskCancelledEvent)
        assert str(event.task_id) == task_id


def _committed_pod(node: str, at: str | None, labels: dict[str, str]) -> dict[str, Any]:
    record: dict[str, Any] = {"image": "registry/x:1", "labels": labels}
    if at is not None:
        record["committedAt"] = at
    return {
        "metadata": {"annotations": {ANNOTATION_COMMITTED_IMAGE: json.dumps(record)}},
        "spec": {"nodeName": node},
    }


class TestNewestCommit:
    def test_the_newest_record_wins_whatever_the_order(self) -> None:
        pods = [
            _committed_pod("n1", "2026-11-22T10:00:00+00:00", {"v": "old"}),
            _committed_pod("n2", "2026-11-22T11:00:00+00:00", {"v": "new"}),
            _committed_pod("n3", None, {"v": "untimed"}),
        ]
        assert newest_commit(pods, "registry/x:1") == ("n2", {"v": "new"})
        assert newest_commit(list(reversed(pods)), "registry/x:1") == ("n2", {"v": "new"})

    def test_another_image_is_not_found(self) -> None:
        pods = [_committed_pod("n1", "2026-11-22T10:00:00+00:00", {})]
        assert newest_commit(pods, "registry/y:1") is None
