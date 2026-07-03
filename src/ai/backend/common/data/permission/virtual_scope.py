from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.entity.types import EntityType, ScopeType
from ai.backend.common.identifier.virtual_scope import VirtualScopeID

__all__ = (
    "VirtualScopeData",
    "ScopeBindingData",
    "EntityMembershipData",
)


@dataclass(frozen=True)
class VirtualScopeData:
    id: VirtualScopeID
    scope_type: ScopeType
    scope_id: str


@dataclass(frozen=True)
class ScopeBindingData:
    """Inbound edge ``real scope -> virtual_scope``: a traditional scope
    (domain/project/user/...) bound to a virtual scope so it can reach
    everything the VS owns. Many scopes may bind to the same VS.

    ``permission_cap`` is the ceiling this hop grants (``None`` = no ceiling);
    effective permission is clipped by a bitwise AND with the cap.
    """

    scope_type: ScopeType
    scope_id: str
    virtual_scope_id: VirtualScopeID
    permission_cap: Permission | None


@dataclass(frozen=True)
class EntityMembershipData:
    """Outbound edge ``virtual_scope -> entity``: an entity that is a member of
    a virtual scope. Attaching one entity here exposes it to every scope bound
    to the same VS.

    ``permission_cap`` is the ceiling this hop grants (``None`` = no ceiling);
    effective permission is clipped by a bitwise AND with the cap.
    """

    virtual_scope_id: VirtualScopeID
    entity_type: EntityType
    entity_id: str
    permission_cap: Permission | None
