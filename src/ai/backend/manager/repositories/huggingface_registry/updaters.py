"""UpdaterSpec implementations for HuggingFace registry repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class HuggingFaceRegistryUpdaterSpec(UpdaterSpec[HuggingFaceRegistryRow]):
    """UpdaterSpec for HuggingFace registry updates."""

    url: OptionalState[str] = field(default_factory=OptionalState.nop)
    token: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[HuggingFaceRegistryRow]:
        return HuggingFaceRegistryRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.url.update_dict(to_update, "url")
        self.token.update_dict(to_update, "token")
        return to_update
