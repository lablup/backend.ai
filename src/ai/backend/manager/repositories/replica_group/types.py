"""Repository-layer input types for replica group reconcile operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field

from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater, Updater
from ai.backend.manager.repositories.scheduling_history.creators import (
    ReplicaGroupHistoryCreatorSpec,
)


@dataclass
class RevisionReplicaCount:
    """Active route counts for one (group, revision): warming+serving vs serving only."""

    live: int
    serving: int


@dataclass
class ReplicaGroupScalingReconcileApply:
    """Everything one scaling-reconcile tick writes, applied in a single transaction.

    Route scale-out creators carry their own RBAC scope; ``drain_updater`` flips
    excess routes to TERMINATING. Group status moves via ``group_updaters``; history
    is either inserted (``new_history_specs``) or merged (``merge_history_ids``).
    """

    scale_out_creators: Sequence[RBACEntityCreator[RoutingRow]] = field(default_factory=list)
    drain_updater: BatchUpdater[RoutingRow] | None = None
    group_updaters: Sequence[Updater[ReplicaGroupRow]] = field(default_factory=list)
    new_history_specs: Sequence[ReplicaGroupHistoryCreatorSpec] = field(default_factory=list)
    merge_history_ids: Sequence[uuid.UUID] = field(default_factory=list)
