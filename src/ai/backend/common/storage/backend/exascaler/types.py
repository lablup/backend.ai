from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult
from ai.backend.common.storage.client.exascaler.types import LustreServerConnection


@dataclass(frozen=True)
class EXAScalerBackendStatusResult(StorageStatusResult):
    """The Lustre servers this host's client reported, null where the observation failed."""

    lfs_version: str | None
    servers: tuple[LustreServerConnection, ...] | None
