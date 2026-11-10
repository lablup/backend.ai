"""Read-write replica-group ops: the reconcile writes plus the reconcile-side reads."""

from __future__ import annotations

from ai.backend.manager.repositories.ops.v2.reconciler.write import ReconcileWriteOps
from ai.backend.manager.repositories.ops.v2.replica_group.query import ReplicaGroupQueryOps


class ReplicaGroupWriteOps(ReplicaGroupQueryOps, ReconcileWriteOps):
    """The reconcile write ops plus the reconcile-side reads."""
