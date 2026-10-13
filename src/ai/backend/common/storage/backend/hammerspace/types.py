from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.storage.types import StorageStatusResult
from ai.backend.common.storage.client.hammerspace.types import HammerspaceSite


@dataclass(frozen=True)
class HammerspaceBackendStatusResult(StorageStatusResult):
    """The sites the Hammerspace API listed, null where the observation failed."""

    sites: tuple[HammerspaceSite, ...] | None
