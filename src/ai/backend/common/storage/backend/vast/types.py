from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult


@dataclass(frozen=True)
class VASTBackendStatusResult(StorageStatusResult):
    """What the VAST API returned, null where the observation failed."""

    cluster_name: str | None
    state: str | None
    guid: str | None
