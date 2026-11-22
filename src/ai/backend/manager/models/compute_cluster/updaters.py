"""DataUpdater implementations for compute clusters."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData, ComputeClusterStatus
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.compute_cluster.searchable_fields import (
    ComputeClusterSearchableFields,
)
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ComputeClusterUpdater(DataUpdater[ComputeClusterRow, ComputeClusterData]):
    """``kubeconfig`` is already encrypted for its column. A status change stamps
    ``status_changed_at``."""

    compute_cluster_id: ComputeClusterID
    description: TriState[str] = field(default_factory=TriState[str].nop)
    api_server: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    kubeconfig: OptionalState[SecretValue] = field(
        default_factory=OptionalState[SecretValue].nop, repr=False
    )
    namespace_prefix: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    gateway_addr: TriState[str] = field(default_factory=TriState[str].nop)
    gateway_public_key: TriState[str] = field(default_factory=TriState[str].nop)
    status: OptionalState[ComputeClusterStatus] = field(
        default_factory=OptionalState[ComputeClusterStatus].nop
    )

    @property
    @override
    def row_class(self) -> type[ComputeClusterRow]:
        return ComputeClusterRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ComputeClusterRow.id

    @override
    def target_id_value(self) -> ComputeClusterID:
        return self.compute_cluster_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.description.update_dict(to_update, "description")
        self.api_server.update_dict(to_update, "api_server")
        self.kubeconfig.update_dict(to_update, "kubeconfig")
        self.namespace_prefix.update_dict(to_update, "namespace_prefix")
        self.gateway_addr.update_dict(to_update, "gateway_addr")
        self.gateway_public_key.update_dict(to_update, "gateway_public_key")
        self.status.update_dict(to_update, "status")
        if "status" in to_update:
            to_update["status_changed_at"] = sa.func.now()
        return to_update

    @override
    def to_data(self, row: ComputeClusterRow) -> ComputeClusterData:
        return ComputeClusterSearchableFields.own.to_data(row)
