"""A finished kernel's container log, handed to the Manager as the Agent does: chunks in Valkey,
then `DoSyncKernelLogsEvent`; the Manager stores it in `kernels.container_log`.

The hand-off is at least once: the termination is recorded after the log and the events are
sent, so a restart in between sends them again. It is idempotent per container: each attempt
replaces the container's chunks instead of appending to them, and the Manager overwrites the
stored log with what it reads.
"""

from __future__ import annotations

import logging
from typing import Final

from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.kernel.anycast import DoSyncKernelLogsEvent
from ai.backend.common.log.types import ContainerLogData, ContainerLogType
from ai.backend.common.types import KernelId
from ai.backend.kube.controller.naming import KERNEL_CONTAINER
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

LOG_CHUNK_SIZE: Final = 64 * 1024
LOG_LIMIT_BYTES: Final = 10 * 1024 * 1024  # what the Manager keeps of a log
LOG_READ_TIMEOUT: Final = 30.0


class KernelLogSync:
    _core: client.CoreV1Api
    _valkey: ValkeyContainerLogClient
    _producer: EventProducer

    def __init__(
        self, api: client.ApiClient, valkey: ValkeyContainerLogClient, producer: EventProducer
    ) -> None:
        self._core = client.CoreV1Api(api)
        self._valkey = valkey
        self._producer = producer

    async def sync(
        self, namespace: str, pod_name: str, kernel_id: KernelId, container_id: str
    ) -> None:
        """Best effort for a Pod already gone: no event, so a log stored by an earlier attempt
        stays. A timeout or a server error raises and the reconcile is retried."""
        try:
            text = await self._core.read_namespaced_pod_log(
                pod_name,
                namespace,
                container=KERNEL_CONTAINER,
                limit_bytes=LOG_LIMIT_BYTES,
                _request_timeout=LOG_READ_TIMEOUT,
            )
        except ApiException as e:
            if e.status is not None and e.status >= 500:
                raise
            log.debug("kernel log not readable", pod_name=pod_name, status=e.status)
            return
        data = text.encode()
        await self._valkey.clear_container_logs(container_id)
        for offset in range(0, len(data), LOG_CHUNK_SIZE):
            await self._valkey.enqueue_container_logs(
                container_id,
                ContainerLogData.from_log(
                    ContainerLogType.ZLIB, data[offset : offset + LOG_CHUNK_SIZE]
                ),
            )
        await self._producer.anycast_event(
            DoSyncKernelLogsEvent(kernel_id=kernel_id, container_id=container_id)
        )
