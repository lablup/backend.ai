from __future__ import annotations

from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.storage.types import StorageStatusResult
from ai.backend.common.storage.abc import AbstractStatusCheck


class AbstractBackendStatusCheck[TResult: StorageStatusResult](
    AbstractStatusCheck[StorageBackendID, TResult]
):
    """A status check of one storage backend, identified by its ``StorageBackendID``."""
