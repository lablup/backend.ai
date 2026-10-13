from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.abc import AbstractBackendStatusCheck
from ai.backend.common.storage.backend.purestorage.types import PureStorageBackendStatusResult
from ai.backend.common.storage.client.purestorage.client import PureStorageClient
from ai.backend.common.storage.client.purestorage.types import PureStorageArray
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class PureStorageBackendStatusCheckArgs:
    backend_id: StorageBackendID
    client: PureStorageClient


class PureStorageBackendStatusCheck(AbstractBackendStatusCheck[PureStorageBackendStatusResult]):
    """Logs in to the Purity API and reads the array it serves."""

    _backend_id: StorageBackendID
    _client: PureStorageClient
    _latest: PureStorageBackendStatusResult | None

    def __init__(self, args: PureStorageBackendStatusCheckArgs) -> None:
        self._backend_id = args.backend_id
        self._client = args.client
        self._latest = None

    @override
    def id(self) -> StorageBackendID:
        return self._backend_id

    @override
    def latest(self) -> PureStorageBackendStatusResult | None:
        return self._latest

    @override
    def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        array: PureStorageArray | None = None
        error_msg: str | None = None
        try:
            array = self._client.get_array()
        except Exception as e:
            log.exception(
                "storage backend status check failed",
                backend_id=str(self._backend_id),
            )
            error_msg = str(e)
        self._latest = PureStorageBackendStatusResult(
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
            array_id=array.array_id if array is not None else None,
            array_name=array.array_name if array is not None else None,
            os=array.os if array is not None else None,
            version=array.version if array is not None else None,
        )
