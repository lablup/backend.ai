from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.kube.controller import cache as cache_module
from ai.backend.kube.controller.cache import ClusterKind, ClusterObjectCache
from ai.backend.kube.controller.runner import needs_resync


def _obj(name: str) -> dict[str, Any]:
    return {"metadata": {"name": name}}


class TestClusterObjectCache:
    async def test_relist_replaces_and_events_update(self) -> None:
        cache = ClusterObjectCache(MagicMock())
        relist = cache._relister(ClusterKind.DEVICE_PROFILES)
        handle = cache._handler(ClusterKind.DEVICE_PROFILES)
        relist([_obj("a"), _obj("b")])
        handle("ADDED", _obj("c"))
        handle("DELETED", _obj("a"))
        names = {o["metadata"]["name"] for o in await cache.items(ClusterKind.DEVICE_PROFILES)}
        assert names == {"b", "c"}

    async def test_reading_before_the_first_list_times_out(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cache_module, "SYNC_TIMEOUT_SECONDS", 0.01)
        with pytest.raises(TimeoutError):
            await ClusterObjectCache(MagicMock()).items(ClusterKind.RESOURCE_SLICES)


class TestNeedsResync:
    @pytest.mark.parametrize(
        ("workload", "expected"),
        [
            ({"metadata": {}}, True),
            ({"metadata": {}, "status": {"phase": "Running"}}, True),
            ({"metadata": {}, "status": {"phase": "Terminated"}}, False),
            ({"metadata": {}, "status": {"phase": "Error"}}, False),
            ({"metadata": {"deletionTimestamp": "x"}, "status": {"phase": "Error"}}, True),
        ],
    )
    def test_ended_sessions_wait_for_deletion(
        self, workload: dict[str, Any], expected: bool
    ) -> None:
        assert needs_resync(workload) is expected
