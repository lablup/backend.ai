"""Cluster-scoped objects the reconciler reads on every session, kept current by watches."""

from __future__ import annotations

import asyncio
import enum
from collections.abc import Callable, Coroutine
from typing import Any, Final

from kubernetes_asyncio import client

from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.device import DeviceProfile
from ai.backend.kube.crd.storage import StorageBinding
from ai.backend.kube.watch import watch_forever

DRA_GROUP: Final = "resource.k8s.io"
DRA_VERSION: Final = "v1"
SYNC_TIMEOUT_SECONDS: Final = 30.0


class ClusterKind(enum.StrEnum):
    STORAGE_BINDINGS = "storagebindings"
    DEVICE_PROFILES = "deviceprofiles"
    RESOURCE_SLICES = "resourceslices"


_GROUP_VERSION: Final = {
    ClusterKind.STORAGE_BINDINGS: (StorageBinding.crd.group, CRD_VERSION),
    ClusterKind.DEVICE_PROFILES: (DeviceProfile.crd.group, CRD_VERSION),
    ClusterKind.RESOURCE_SLICES: (DRA_GROUP, DRA_VERSION),
}


def list_call(
    custom: client.CustomObjectsApi, kind: ClusterKind
) -> Callable[..., Coroutine[Any, Any, Any]]:
    group, version = _GROUP_VERSION[kind]
    return lambda **kw: custom.list_cluster_custom_object(group, version, str(kind), **kw)


class ClusterObjectCache:
    """Object name → object (plain dict), by kind. Readers wait for the first full list."""

    _custom: client.CustomObjectsApi
    _objects: dict[ClusterKind, dict[str, dict[str, Any]]]
    _synced: dict[ClusterKind, asyncio.Event]

    def __init__(self, api: client.ApiClient) -> None:
        self._custom = client.CustomObjectsApi(api)
        self._objects = {kind: {} for kind in ClusterKind}
        self._synced = {kind: asyncio.Event() for kind in ClusterKind}

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for kind in ClusterKind:
                tg.create_task(
                    watch_forever(
                        list_call(self._custom, kind),
                        self._handler(kind),
                        on_relist=self._relister(kind),
                    )
                )

    async def items(self, kind: ClusterKind) -> list[dict[str, Any]]:
        await asyncio.wait_for(self._synced[kind].wait(), SYNC_TIMEOUT_SECONDS)
        return list(self._objects[kind].values())

    def _relister(self, kind: ClusterKind) -> Callable[[list[dict[str, Any]]], None]:
        def relist(items: list[dict[str, Any]]) -> None:
            self._objects[kind] = {item["metadata"]["name"]: item for item in items}
            self._synced[kind].set()

        return relist

    def _handler(self, kind: ClusterKind) -> Callable[[str, dict[str, Any]], None]:
        def handle(event: str, obj: dict[str, Any]) -> None:
            name = obj["metadata"]["name"]
            if event == "DELETED":
                self._objects[kind].pop(name, None)
            else:
                self._objects[kind][name] = obj

        return handle
