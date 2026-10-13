from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult


@dataclass(frozen=True)
class PureStorageBackendStatusResult(StorageStatusResult):
    """What the Purity array API returned, null where the observation failed."""

    array_id: str | None
    array_name: str | None
    os: str | None
    version: str | None
