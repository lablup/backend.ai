from __future__ import annotations

from dataclasses import dataclass, field

from ai.backend.manager.types import OptionalState


@dataclass
class ArtifactStorageCreatorMeta:
    name: str


@dataclass
class ArtifactStorageModifierMeta:
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
