"""Upserter input for RBAC ops entity upserts, addressed with the open entity types.

Successor of the ``RBACElementType``/``RBACElementRef``-keyed
:class:`ai.backend.manager.repositories.base.rbac.entity_upserter.RBACEntityUpserter`;
see :mod:`.creator` for the design.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityRef
from ai.backend.manager.models.base import Base
from ai.backend.manager.repositories.base.rbac.entity.types import ScopeMembership
from ai.backend.manager.repositories.base.rbac.entity_upserter import ConflictTarget
from ai.backend.manager.repositories.base.upserter import UpserterSpec


class EntityUpserter[TRow: Base](ABC):
    """A row to upsert (INSERT ON CONFLICT UPDATE) and the scopes a newly inserted
    row joins as a member.

    ``membership_on_create`` applies only when the upsert inserts a new row; a
    conflict-updated row keeps its existing memberships untouched. As with
    :meth:`EntityCreator.membership`, the RBAC ops layer performs the enrollment.
    """

    @abstractmethod
    def spec(self) -> UpserterSpec[TRow]:
        """Return the spec defining the insert/update values."""
        raise NotImplementedError

    @abstractmethod
    def conflict_target(self) -> ConflictTarget:
        """Return the unique index ON CONFLICT arbitrates on."""
        raise NotImplementedError

    @abstractmethod
    def entity_ref_of(self, row: TRow) -> EntityRef:
        """Return the upserted row's entity reference, used to address it in the
        membership edges."""
        raise NotImplementedError

    @abstractmethod
    def membership_on_create(self, row: TRow) -> Sequence[ScopeMembership]:
        """Return the membership edges a newly inserted row joins by."""
        raise NotImplementedError
