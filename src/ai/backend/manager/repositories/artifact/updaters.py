"""UpdaterSpec implementations for artifact repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.base.types import QueryCondition
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import TriState


@dataclass
class ArtifactUpdaterSpec(UpdaterSpec[ArtifactRow]):
    """UpdaterSpec for artifact updates."""

    readonly: TriState[bool] = field(default_factory=TriState[bool].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ArtifactRow]:
        return ArtifactRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.readonly.update_dict(to_update, "readonly")
        self.description.update_dict(to_update, "description")
        return to_update

    @override
    def guard_condition(self) -> QueryCondition | None:
        return None

    @override
    def not_found_error(self) -> BackendAIError | None:
        return None

    @override
    def on_guard_failure(self) -> BackendAIError | None:
        return None
