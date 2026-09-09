"""Scope attributes exposed to role name templates."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityID


@dataclass(frozen=True)
class ScopeTemplateValue:
    """Scope attributes exposed to templates as ``{{ scope.* }}``."""

    id: EntityID
    name: str
    type: str
