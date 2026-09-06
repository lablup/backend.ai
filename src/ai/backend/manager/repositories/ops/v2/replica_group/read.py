"""Read-only replica-group ops: the v2 read paths plus the reconcile-side reads."""

from __future__ import annotations

from ai.backend.manager.repositories.ops.v2.read import V2ReadOps
from ai.backend.manager.repositories.ops.v2.replica_group.query import ReplicaGroupQueryOps


class ReplicaGroupReadOps(ReplicaGroupQueryOps, V2ReadOps):
    """The general v2 read ops plus the reconcile-side reads."""
