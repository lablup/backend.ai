from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult


@dataclass(frozen=True)
class GPFSBackendStatusResult(StorageStatusResult):
    """What the Spectrum Scale management API returned, null where the observation failed."""

    cluster_name: str | None
    cluster_id: str | None
