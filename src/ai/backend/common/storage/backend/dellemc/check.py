from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.abc import AbstractBackendStatusCheck
from ai.backend.common.storage.backend.dellemc.types import DellEMCOneFSBackendStatusResult
from ai.backend.common.storage.client.dellemc.client import DellEMCOneFSClient
from ai.backend.common.storage.client.dellemc.types import OneFSCluster
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class DellEMCOneFSBackendStatusCheckArgs:
    backend_id: StorageBackendID
    client: DellEMCOneFSClient


class DellEMCOneFSBackendStatusCheck(AbstractBackendStatusCheck[DellEMCOneFSBackendStatusResult]):
    """Reads the cluster configuration from the OneFS platform API."""

    _backend_id: StorageBackendID
    _client: DellEMCOneFSClient
    _latest: DellEMCOneFSBackendStatusResult | None

    def __init__(self, args: DellEMCOneFSBackendStatusCheckArgs) -> None:
        self._backend_id = args.backend_id
        self._client = args.client
        self._latest = None

    @override
    def id(self) -> StorageBackendID:
        return self._backend_id

    @override
    def latest(self) -> DellEMCOneFSBackendStatusResult | None:
        return self._latest

    @override
    def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        cluster: OneFSCluster | None = None
        error_msg: str | None = None
        try:
            cluster = self._client.get_cluster()
        except Exception as e:
            log.exception(
                "storage backend status check failed",
                backend_id=str(self._backend_id),
            )
            error_msg = str(e)
        self._latest = DellEMCOneFSBackendStatusResult(
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
            cluster_name=cluster.cluster_name if cluster is not None else None,
            release=cluster.release if cluster is not None else None,
            build=cluster.build if cluster is not None else None,
        )
