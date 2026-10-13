from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.storage.backend.abc import AbstractBackendStatusCheck
from ai.backend.common.storage.backend.exascaler.types import EXAScalerBackendStatusResult
from ai.backend.common.storage.client.exascaler.client import EXAScalerClient
from ai.backend.common.storage.client.exascaler.types import LustreServerConnection
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class EXAScalerBackendStatusCheckArgs:
    backend_id: StorageBackendID
    client: EXAScalerClient


class EXAScalerBackendStatusCheck(AbstractBackendStatusCheck[EXAScalerBackendStatusResult]):
    """Asks this host's Lustre client whether it reaches each MDT and OST it has mounted."""

    _backend_id: StorageBackendID
    _client: EXAScalerClient
    _latest: EXAScalerBackendStatusResult | None

    def __init__(self, args: EXAScalerBackendStatusCheckArgs) -> None:
        self._backend_id = args.backend_id
        self._client = args.client
        self._latest = None

    @override
    def id(self) -> StorageBackendID:
        return self._backend_id

    @override
    def latest(self) -> EXAScalerBackendStatusResult | None:
        return self._latest

    @override
    def check_status(self) -> None:
        started_at = datetime.now(UTC)
        start_counter = time.perf_counter()
        lfs_version: str | None = None
        servers: tuple[LustreServerConnection, ...] | None = None
        error_msg: str | None = None
        try:
            lfs_version = self._client.get_lfs_version()
            servers = self._client.check_servers()
        except subprocess.CalledProcessError as e:
            log.exception(
                "storage backend status check failed",
                backend_id=str(self._backend_id),
            )
            error_msg = f"{e}: {e.stderr.strip()}"
        except Exception as e:
            log.exception(
                "storage backend status check failed",
                backend_id=str(self._backend_id),
            )
            error_msg = str(e)
        self._latest = EXAScalerBackendStatusResult(
            check_started_at=started_at,
            duration=timedelta(seconds=time.perf_counter() - start_counter),
            error_msg=error_msg,
            lfs_version=lfs_version,
            servers=servers,
        )
