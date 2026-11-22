"""Session commit and image push for the Manager's convert-to-image: the node helper of the
kernel's node does the work, the gateway answers as the Agent does (a bgtask id, then a bgtask
done or failed event that the Manager waits for).
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Awaitable, Mapping
from typing import Any, Final

import aiohttp
from kubernetes_asyncio import client

from ai.backend.common.docker import ImageRef
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BgtaskDoneEvent,
    BgtaskFailedEvent,
)
from ai.backend.common.events.types import EventCacheDomain
from ai.backend.kube.controller.naming import (
    KERNEL_CONTAINER,
    LABEL_KERNEL_ID,
    LABEL_MANAGED_BY,
    MANAGED_BY,
)
from ai.backend.kube.errors import NodeHelperCommandError
from ai.backend.kube.gateway.kernel_index import KernelIndex
from ai.backend.kube.nodehelper.server import TOKEN_HEADER
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

NODE_HELPER_SELECTOR: Final = "app.kubernetes.io/name=node-helper"
# On the kernel Pod: {"image": <canonical>, "labels": {...}} of its last commit. The push
# finds the node holding the commit through it, after a gateway restart too.
ANNOTATION_COMMITTED_IMAGE: Final = "backend.ai/committed-image"
_TIMEOUT: Final = aiohttp.ClientTimeout(total=1800)


class GatewayImages:
    _core: client.CoreV1Api
    _api: client.ApiClient
    _index: KernelIndex
    _producer: EventProducer
    _namespace: str
    _port: int
    _token: str
    _tasks: set[asyncio.Task[None]]

    def __init__(
        self,
        api: client.ApiClient,
        index: KernelIndex,
        producer: EventProducer,
        *,
        namespace: str,
        port: int,
        token: str,
    ) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._index = index
        self._producer = producer
        self._namespace = namespace
        self._port = port
        self._token = token
        self._tasks = set()

    def commit(self, kernel_id: str, canonical: str, labels: Mapping[str, str]) -> str:
        return self._start(self._commit(kernel_id, canonical, labels))

    def push(self, image_ref: ImageRef, registry: Mapping[str, Any]) -> str:
        return self._start(self._push(image_ref, registry))

    async def _commit(self, kernel_id: str, canonical: str, labels: Mapping[str, str]) -> None:
        endpoint = self._index.get(kernel_id)
        if endpoint is None:
            raise NodeHelperCommandError(f"kernel {kernel_id} is not running here")
        pod = await self._core.read_namespaced_pod(endpoint.pod_name, endpoint.namespace)
        statuses = pod.status.container_statuses or []
        container = next((c for c in statuses if c.name == KERNEL_CONTAINER), None)
        if container is None or not container.container_id:
            raise NodeHelperCommandError(f"kernel {kernel_id} has no running container")
        await self._call(
            pod.spec.node_name,
            "commit",
            {"container_id": container.container_id.split("://", 1)[-1], "image": canonical},
        )
        record = json.dumps({"image": canonical, "labels": dict(labels)}, sort_keys=True)
        await self._core.patch_namespaced_pod(
            endpoint.pod_name,
            endpoint.namespace,
            {"metadata": {"annotations": {ANNOTATION_COMMITTED_IMAGE: record}}},
        )

    async def _committed_on(self, canonical: str) -> tuple[str, dict[str, str]]:
        """The node and labels of the kernel Pod whose last commit is `canonical`."""
        pods = await self._core.list_pod_for_all_namespaces(
            label_selector=f"{LABEL_MANAGED_BY}={MANAGED_BY}"
        )
        for raw in pods.items:
            pod = self._api.sanitize_for_serialization(raw)
            meta = pod["metadata"]
            endpoint = self._index.get((meta.get("labels") or {}).get(LABEL_KERNEL_ID, ""))
            if endpoint is None or endpoint.pod_uid != meta.get("uid"):
                continue  # not a kernel Pod the index trusts
            try:
                record = json.loads((meta.get("annotations") or {})[ANNOTATION_COMMITTED_IMAGE])
            except (KeyError, ValueError):
                continue
            node = pod.get("spec", {}).get("nodeName")
            if isinstance(record, dict) and record.get("image") == canonical and node:
                labels = record.get("labels") or {}
                return str(node), {str(k): str(v) for k, v in labels.items()}
        raise NodeHelperCommandError(f"{canonical} was not committed here")

    async def _push(self, image_ref: ImageRef, registry: Mapping[str, Any]) -> None:
        node, labels = await self._committed_on(image_ref.canonical)
        url = str(registry.get("url", ""))
        await self._call(
            node,
            "push",
            {
                "image": image_ref.canonical,
                "username": registry.get("username"),
                "password": registry.get("password"),
                "insecure": url.startswith("http://") or not registry.get("ssl_verify", True),
                "labels": labels,
            },
        )

    async def _call(self, node: str, action: str, body: Mapping[str, Any]) -> None:
        helpers = await self._core.list_namespaced_pod(
            self._namespace,
            label_selector=NODE_HELPER_SELECTOR,
            field_selector=f"spec.nodeName={node}",
        )
        ready = [p for p in helpers.items if p.status.pod_ip and p.status.phase == "Running"]
        if not ready:
            raise NodeHelperCommandError(f"no node helper runs on {node}")
        url = f"http://{ready[0].status.pod_ip}:{self._port}/v1/{action}"
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as http:
            async with http.post(url, json=body, headers={TOKEN_HEADER: self._token}) as resp:
                answer = await resp.json(content_type=None)
                if resp.status != 200:
                    error = answer.get("error") if isinstance(answer, dict) else None
                    raise NodeHelperCommandError(str(error or f"HTTP {resp.status}"))

    def _start(self, work: Awaitable[None]) -> str:
        task_id = uuid.uuid4()

        async def run() -> None:
            cache_id = EventCacheDomain.BGTASK.cache_id(str(task_id))
            try:
                await work
            except (
                NodeHelperCommandError,
                aiohttp.ClientError,
                client.ApiException,
                ValueError,
            ) as e:
                message = str(e.extra_msg) if isinstance(e, NodeHelperCommandError) else repr(e)
                log.trace("image task failed", task_id=str(task_id), reason=message)
                await self._producer.broadcast_event_with_cache(
                    cache_id, BgtaskFailedEvent(task_id=task_id, message=message)
                )
                return
            await self._producer.broadcast_event_with_cache(
                cache_id, BgtaskDoneEvent(task_id=task_id, message=None)
            )

        task = asyncio.create_task(run())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return str(task_id)
