"""The membership record the entity writes carry to the ops layer."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityRef, ScopeRef


@dataclass(frozen=True)
class ScopeMembershipEntry:
    """A member row under its parent scope."""

    member: EntityRef
    parent_scope: ScopeRef
