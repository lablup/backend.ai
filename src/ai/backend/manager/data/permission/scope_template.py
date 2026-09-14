"""Scope attributes exposed to role name templates."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ScopeTemplateValue:
    """Scope attributes exposed to templates as ``{{ scope.* }}``."""

    id: UUID
    name: str
    type: str
