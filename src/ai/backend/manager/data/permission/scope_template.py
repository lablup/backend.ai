"""Scope attributes exposed to role name templates."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.identifier.scope import ScopeID


@dataclass(frozen=True)
class ScopeTemplateValue:
    """Scope attributes exposed to templates as ``{{ scope.* }}``."""

    id: ScopeID
    name: str
    type: str
