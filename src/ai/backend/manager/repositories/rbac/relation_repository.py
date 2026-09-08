"""The links between two entities, written through the relation ops.

One method per direction and none per kind: which relation a link is is the spec's, and
the spec is chosen where the request is read.
"""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider

__all__ = ("RbacRelationRepository",)


class RbacRelationRepository:
    """Every link this system writes between two entities."""

    _ops: RelationOpsProvider

    def __init__(self, ops_provider: RelationOpsProvider) -> None:
        self._ops = ops_provider

    async def create[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        pairs: Sequence[tuple[TScope, TTarget]],
        creator: RelationCreator[TScope, TTarget, TRow],
    ) -> list[bool]:
        """Let each scope reach its target and what it owns. Answers per pair whether
        the link was written; one already standing is left alone."""
        async with self._ops.write_ops() as w:
            return await w.create_relations(creator, pairs)

    async def purge[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        pairs: Sequence[tuple[TScope, TTarget]],
        purger: RelationPurger[TScope, TTarget, TRow],
    ) -> list[bool]:
        """Take that reach back. Answers per pair whether it was linked."""
        async with self._ops.write_ops() as w:
            return await w.purge_relations(purger, pairs)

    async def delete[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        pairs: Sequence[tuple[TScope, TTarget]],
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
    ) -> list[bool]:
        """Switch each pair off, leaving what each side reads of the other. Answers per
        pair whether the row moved."""
        async with self._ops.write_ops() as w:
            return await w.delete_relations(updater, pairs)

    async def restore[TScope: EntityIdentifier, TTarget: EntityIdentifier, TRow: Base](
        self,
        pairs: Sequence[tuple[TScope, TTarget]],
        updater: RelationLifecycleUpdater[TScope, TTarget, TRow],
    ) -> list[bool]:
        """Switch each pair back on. Answers as :meth:`delete` does."""
        async with self._ops.write_ops() as w:
            return await w.restore_relations(updater, pairs)
