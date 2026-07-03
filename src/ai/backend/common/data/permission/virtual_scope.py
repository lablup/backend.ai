from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.entity.types import EntityRef, EntityType, ScopeRef, ScopeType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID

__all__ = (
    "VirtualScopeData",
    "ScopeBindingData",
    "EntityMembershipData",
    "VirtualScopeReach",
)


@dataclass(frozen=True)
class VirtualScopeData:
    id: VirtualScopeID
    scope_type: ScopeType
    scope_id: ScopeID


@dataclass(frozen=True)
class ScopeBindingData:
    """Inbound edge ``real scope -> virtual_scope``: a traditional scope
    (domain/project/user/...) bound to a virtual scope so it can reach
    everything the VS owns. Many scopes may bind to the same VS.

    ``permission_cap`` is the ceiling this hop grants (``None`` = no ceiling);
    effective permission is clipped by a bitwise AND with the cap.
    """

    scope_type: ScopeType
    scope_id: ScopeID
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
    entity_id: EntityID
    permission_cap: Permission | None


@dataclass(frozen=True)
class VirtualScopeReach:
    """One resolved ``scope -> virtual_scope -> entity`` path.

    Carries both hop caps *unclipped*; the caller clips the effective permission by
    bitwise-ANDing ``binding_cap`` and ``membership_cap`` (``None`` means no ceiling
    at that hop).
    """

    virtual_scope_id: VirtualScopeID
    scope: ScopeRef
    entity: EntityRef
    binding_cap: Permission | None  # real scope -> virtual_scope hop
    membership_cap: Permission | None  # virtual_scope -> entity hop
