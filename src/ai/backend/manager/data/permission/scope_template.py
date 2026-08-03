"""Scope attributes exposed to role name templates."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ai.backend.common.identifier.scope import ScopeID


class ScopeTemplateValue(BaseModel):
    """Scope attributes exposed to templates as ``{{ scope.* }}``."""

    model_config = ConfigDict(frozen=True)

    id: ScopeID
    name: str
    type: str
