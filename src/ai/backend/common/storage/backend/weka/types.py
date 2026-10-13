from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult


@dataclass(frozen=True)
class WekaBackendStatusResult(StorageStatusResult):
    """What the Weka API returned, null where the observation failed."""

    cluster_name: str | None
    status: str | None
    release: str | None
