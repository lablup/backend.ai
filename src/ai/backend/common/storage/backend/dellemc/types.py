from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult


@dataclass(frozen=True)
class DellEMCOneFSBackendStatusResult(StorageStatusResult):
    """What the OneFS platform API returned, null where the observation failed."""

    cluster_name: str | None
    release: str | None
    build: str | None
