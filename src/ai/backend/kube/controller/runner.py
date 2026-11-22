"""Watch SessionWorkloads and their Pods, and feed a deduplicated work queue."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from typing import Any, Final

from kubernetes_asyncio import client

from ai.backend.kube.controller.cache import ClusterObjectCache
from ai.backend.kube.controller.naming import LABEL_MANAGED_BY, MANAGED_BY
from ai.backend.kube.controller.reconciler import SessionReconciler
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.session import SessionPhase, SessionWorkload
from ai.backend.kube.watch import watch_forever
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_SW = SessionWorkload.crd

Key = tuple[str, str]  # (namespace, name)
_ENDED: Final = frozenset({SessionPhase.ERROR.value, SessionPhase.TERMINATED.value})
_RESYNC_TIMEOUT: Final = 60.0
# A failed reconcile is retried after 1, 2, 4, ... seconds, at most this long.
_RETRY_BASE_SECONDS: Final = 1.0
_RETRY_MAX_SECONDS: Final = 60.0


class WorkQueue:
    """A key is queued at most once; a key changed while in progress is processed again."""

    _queue: asyncio.Queue[Key]
    _queued: set[Key]
    _active: set[Key]
    _dirty: set[Key]

    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        self._queued = set()
        self._active = set()
        self._dirty = set()

    def add(self, key: Key) -> None:
        if key in self._active:
            self._dirty.add(key)
            return
        if key not in self._queued:
            self._queued.add(key)
            self._queue.put_nowait(key)

    async def get(self) -> Key:
        key = await self._queue.get()
        self._queued.discard(key)
        self._active.add(key)
        return key

    def done(self, key: Key) -> None:
        self._active.discard(key)
        if key in self._dirty:
            self._dirty.discard(key)
            self.add(key)


class SessionController:
    _api: client.ApiClient
    _reconciler: SessionReconciler
    _queue: WorkQueue
    _workers: int
    _resync_seconds: float
    _cache: ClusterObjectCache | None
    _retries: dict[Key, int]

    def __init__(
        self,
        api: client.ApiClient,
        reconciler: SessionReconciler,
        *,
        workers: int = 4,
        resync_seconds: float = 30.0,
        cache: ClusterObjectCache | None = None,
    ) -> None:
        self._api = api
        self._reconciler = reconciler
        self._cache = cache
        self._queue = WorkQueue()
        self._workers = workers
        self._resync_seconds = resync_seconds
        self._retries = {}

    async def run(self) -> None:
        custom = client.CustomObjectsApi(self._api)
        core = client.CoreV1Api(self._api)
        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                watch_forever(
                    lambda **kw: custom.list_cluster_custom_object(
                        _SW.group, CRD_VERSION, _SW.plural, **kw
                    ),
                    self._on_workload,
                )
            )
            tg.create_task(
                watch_forever(
                    lambda **kw: core.list_pod_for_all_namespaces(
                        label_selector=f"{LABEL_MANAGED_BY}={MANAGED_BY}", **kw
                    ),
                    self._on_owned_object,
                )
            )
            if self._cache is not None:
                tg.create_task(self._cache.run())
            tg.create_task(self._resync_forever(custom))
            for _ in range(self._workers):
                tg.create_task(self._work_forever())

    def _on_workload(self, _event: str, obj: Any) -> None:
        meta = obj["metadata"]
        self._queue.add((meta["namespace"], meta["name"]))

    def _on_owned_object(self, _event: str, obj: Any) -> None:
        meta = obj["metadata"]
        for ref in meta.get("ownerReferences") or []:
            if ref["kind"] == _SW.kind:
                self._queue.add((meta["namespace"], ref["name"]))

    async def _resync_forever(self, custom: client.CustomObjectsApi) -> None:
        """Requeue live sessions; an ended one waits for the Manager to delete it."""
        while True:
            try:
                listed = await custom.list_cluster_custom_object(
                    _SW.group, CRD_VERSION, _SW.plural, _request_timeout=_RESYNC_TIMEOUT
                )
                for item in listed["items"]:
                    if needs_resync(item):
                        self._on_workload("RESYNC", item)
            except Exception as e:
                log.warning("resync list failed", exc_info=e)
            await asyncio.sleep(self._resync_seconds)

    async def _work_forever(self) -> None:
        loop = asyncio.get_running_loop()
        while True:
            key = await self._queue.get()
            try:
                await self._reconciler.reconcile(*key)
            except Exception:
                log.exception("reconcile failed", k8s_namespace=key[0], name=key[1])
                attempts = self._retries.get(key, 0)
                self._retries[key] = attempts + 1
                loop.call_later(retry_delay(attempts), self._queue.add, key)
            else:
                self._retries.pop(key, None)
            finally:
                self._queue.done(key)


def retry_delay(attempts: int) -> float:
    """Seconds before the retry of a reconcile that failed `attempts` times before."""
    backoff: float = _RETRY_BASE_SECONDS * (1 << min(attempts, 16))
    return min(backoff, _RETRY_MAX_SECONDS)


def needs_resync(workload: Mapping[str, Any]) -> bool:
    """A session being deleted, or not ended yet."""
    if workload["metadata"].get("deletionTimestamp"):
        return True
    return (workload.get("status") or {}).get("phase") not in _ENDED
