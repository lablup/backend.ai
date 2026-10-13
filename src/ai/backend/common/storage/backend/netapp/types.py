from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult


@dataclass(frozen=True)
class NetAppBackendStatusResult(StorageStatusResult):
    """What the ONTAP cluster API returned, null where the observation failed."""

    cluster_name: str | None
    cluster_uuid: str | None
    version: str | None
