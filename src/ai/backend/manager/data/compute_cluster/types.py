from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Final, override

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier
from ai.backend.manager.secret.types import SecretValue

__all__ = (
    "ComputeClusterData",
    "ComputeClusterStatus",
)


KUBERNETES_RESOURCE_GROUP_DRIVER: Final = "kubernetes"
"""`scaling_groups.driver` of a resource group whose sessions run in a compute cluster."""


DEFAULT_CLUSTER_SCHEDULER: Final = "sokovan"
"""`driver_opts.scheduler` when unset: the cluster's sokovan places the Pods."""


class ComputeClusterStatus(enum.StrEnum):
    UNKNOWN = "UNKNOWN"  # registered, not contacted yet
    ALIVE = "ALIVE"
    LOST = "LOST"  # the API server cannot be reached; no new sessions are placed


@dataclass(frozen=True)
class ComputeClusterData(EntityData):
    id: ComputeClusterID
    name: str
    description: str | None
    api_server: str
    kubeconfig: SecretValue = field(repr=False)
    namespace_prefix: str
    gateway_addr: str | None
    gateway_public_key: str | None
    status: ComputeClusterStatus
    status_changed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass(frozen=True)
class ProjectQueueData:
    """What a project's queue in a compute cluster carries: its limit and fair share factor."""

    project_id: uuid.UUID
    total_resource_slots: Mapping[str, str]
    fair_share_factor: Decimal | None


@dataclass(frozen=True)
class ResourceGroupComputeCluster:
    """The compute cluster of a `kubernetes` resource group, the scheduler adapter it uses
    there (`driver_opts.scheduler`: sokovan, kueue or kube), and the namespace of the
    cluster's Backend.AI components (`driver_opts.system_namespace`)."""

    cluster: ComputeClusterData
    scheduler: str
    system_namespace: str
