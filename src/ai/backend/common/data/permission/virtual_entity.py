from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import Permission

__all__ = (
    "VirtualEntityData",
    "ScopeBindingData",
    "EntityMembershipData",
)


@dataclass(frozen=True)
class VirtualEntityData:
    id: VirtualEntityID
    entity_type: EntityType
    entity_id: EntityID


@dataclass(frozen=True)
class ScopeBindingData:
    """Inbound edge ``scope -> virtual_entity``: a scope (domain/project/user/...),
    named by its own virtual entity node, bound to a virtual entity so it can reach
    everything the virtual entity owns. Many scopes may bind to the same virtual entity.

    ``permission_cap`` is the ceiling this hop grants (``None`` = no ceiling);
    effective permission is clipped by a bitwise AND with the cap.
    """

    scope_entity_id: VirtualEntityID
    virtual_entity_id: VirtualEntityID
    permission_cap: Permission | None


@dataclass(frozen=True)
class EntityMembershipData:
    """Outbound edge ``virtual_entity -> entity``: an entity, named by its own
    virtual entity node, that is a member of a virtual entity. Attaching one entity
    here exposes it to every scope bound to the same virtual entity.

    ``permission_cap`` is the ceiling this hop grants (``None`` = no ceiling);
    effective permission is clipped by a bitwise AND with the cap.
    """

    virtual_entity_id: VirtualEntityID
    member_entity_id: VirtualEntityID
    permission_cap: Permission | None
