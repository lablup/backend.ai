"""Read-write v2 ops, composed from the per-concern write modules."""

from __future__ import annotations

from ai.backend.manager.repositories.ops.v2.batch_write import V2BatchWriteOps
from ai.backend.manager.repositories.ops.v2.entity_write import V2EntityWriteOps
from ai.backend.manager.repositories.ops.v2.field_write import V2FieldWriteOps
from ai.backend.manager.repositories.ops.v2.global_write import V2GlobalWriteOps
from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.ops.v2.update_write import V2UpdateWriteOps


class V2WriteOps(
    V2EntityWriteOps,
    V2GlobalWriteOps,
    V2FieldWriteOps,
    V2UpdateWriteOps,
    V2BatchWriteOps,
    V2ReadOps,
):
    """Read-write operations over the v2 write specs, bound to a single session.

    Composed by inheritance from the per-concern ops — entity writes (the
    role-managed variants included), global and field writes, family-neutral
    updates, batch writes — on top of the read ops; each concern lives in its
    own module and shares the primitives of ``V2WriteOpsBase``.
    """
