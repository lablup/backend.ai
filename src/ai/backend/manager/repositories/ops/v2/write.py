"""Read-write v2 ops, composed from the per-concern write modules."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Self

from ai.backend.manager.repositories.ops.v2.batch_write import V2BatchWriteOps
from ai.backend.manager.repositories.ops.v2.dangling_field_write import V2DanglingFieldWriteOps
from ai.backend.manager.repositories.ops.v2.entity_write import V2EntityWriteOps
from ai.backend.manager.repositories.ops.v2.field_write import V2FieldWriteOps
from ai.backend.manager.repositories.ops.v2.global_write import V2GlobalWriteOps
from ai.backend.manager.repositories.ops.v2.grant_write import V2GrantWriteOps
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.ops.v2.relation_write import V2RelationWriteOps
from ai.backend.manager.repositories.ops.v2.update_write import V2UpdateWriteOps


class V2WriteOps(
    V2EntityWriteOps,
    V2GlobalWriteOps,
    V2RelationWriteOps,
    V2GrantWriteOps,
    V2FieldWriteOps,
    V2DanglingFieldWriteOps,
    V2UpdateWriteOps,
    V2BatchWriteOps,
    V2ReadOps,
):
    """Read-write operations over the v2 write specs, bound to a single session.

    Composed by inheritance from the per-concern ops — entity writes (the
    role-managed variants included), global, field and sidecar writes, the
    updates, batch writes, the grants over existing entities and the relations
    between them — on top of the
    read ops; each concern lives in its own module and shares the primitives of
    ``V2WriteOpsBase``.

    The reconcile transition is not among them: it belongs to
    ``repositories/ops/v2/reconciler/``, whose ops extend this class.
    """

    @asynccontextmanager
    async def savepoint(self) -> AsyncGenerator[Self]:
        """Open a nested transaction on the same session and yield ops bound to it.

        A failure inside the block rolls back to the savepoint and leaves the
        enclosing transaction usable. Yields the same ops type, so a subclass
        carrying a domain primitive keeps it inside the savepoint.
        """
        async with self._sess.begin_nested():
            yield type(self)(self._sess)
