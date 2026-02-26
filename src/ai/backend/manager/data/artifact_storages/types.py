from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class ArtifactStorageUpdaterSpec(UpdaterSpec[ArtifactStorageRow]):
    """UpdaterSpec for ArtifactStorageRow."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ArtifactStorageRow]:
        return ArtifactStorageRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.name.update_dict(values, "name")
        return values
