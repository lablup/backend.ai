"""Creator input for RBAC ops entity creation, addressed with the open entity types.

Successor of the ``RBACElementType``/``RBACElementRef``-keyed
:class:`ai.backend.manager.repositories.base.rbac.entity_creator.RBACEntityCreator`.
The row insert itself is the plain base create; everything RBAC — scope association,
virtual-scope membership, permission cap — is expressed as :class:`ScopeMembership`
edges and enrolled by the RBAC ops layer, which resolves the virtual scopes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence

from ai.backend.common.data.entity.types import EntityRef
from ai.backend.manager.data.permission.role import ScopeSystemRoleData
from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity.types import ScopeMembership


class EntityCreator[TRow: Base](ABC):
    """A row to create and the membership edges the created entity joins by.

    An empty ``membership`` creates a standalone (GLOBAL) entity: a plain insert
    bound to no scope.
    """

    @abstractmethod
    def spec(self) -> CreatorSpec[TRow]:
        """Return the spec defining the row to create."""
        raise NotImplementedError

    @abstractmethod
    def entity_ref_of(self, row: TRow) -> EntityRef:
        """Return the created row's entity reference, used to address it in the
        membership edges and as the scope identity the entity doubles as."""
        raise NotImplementedError

    @abstractmethod
    def membership(self, row: TRow) -> Sequence[ScopeMembership]:
        """Return the membership edges the created row joins by. Enrollment needs
        virtual-scope resolution, so the RBAC ops layer performs it after the
        insert."""
        raise NotImplementedError

    @abstractmethod
    def system_roles_of(self, row: TRow) -> Collection[ScopeSystemRoleData]:
        """Return the SYSTEM roles to provision for the scope the created entity
        becomes; empty for entities that declare none."""
        raise NotImplementedError
