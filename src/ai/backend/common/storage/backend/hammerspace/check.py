from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.abc import AbstractBackendStatusCheck
from ai.backend.common.storage.backend.hammerspace.types import HammerspaceBackendStatusResult
from ai.backend.common.storage.client.hammerspace.client import HammerspaceClient
from ai.backend.common.storage.client.hammerspace.types import HammerspaceSite
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class HammerspaceBackendStatusCheckArgs:
    backend_id: StorageBackendID
    client: HammerspaceClient


class HammerspaceBackendStatusCheck(AbstractBackendStatusCheck[HammerspaceBackendStatusResult]):
    """Logs in to the Hammerspace API and lists the sites it serves."""

    _backend_id: StorageBackendID
    _client: HammerspaceClient
    _latest: HammerspaceBackendStatusResult | None

    def __init__(self, args: HammerspaceBackendStatusCheckArgs) -> None:
        self._backend_id = args.backend_id
        self._client = args.client
        self._latest = None

    @override
    def id(self) -> StorageBackendID:
        return self._backend_id

    @override
    def latest(self) -> HammerspaceBackendStatusResult | None:
        return self._latest

    @override
    def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        sites: tuple[HammerspaceSite, ...] | None = None
        error_msg: str | None = None
        try:
            sites = self._client.list_sites()
        except Exception as e:
            log.exception(
                "storage backend status check failed",
                backend_id=str(self._backend_id),
            )
            error_msg = str(e)
        self._latest = HammerspaceBackendStatusResult(
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
            sites=sites,
        )
