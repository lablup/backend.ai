from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.errors.compute_cluster import ComputeClusterConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.compute_cluster.searchable_fields import (
    ComputeClusterSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.secret.types import SecretValue


@dataclass
class ComputeClusterCreator(
    CreatedInGlobal[ComputeClusterRow], EntityCreator[ComputeClusterRow, ComputeClusterData]
):
    """Creator for a compute cluster. ``kubeconfig`` is already encrypted for its column."""

    name: str
    description: str | None
    api_server: str
    kubeconfig: SecretValue = field(repr=False)
    namespace_prefix: str
    gateway_addr: str | None
    gateway_public_key: str | None

    @override
    def entity_id(self, row: ComputeClusterRow) -> ComputeClusterID:
        return ComputeClusterID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=ComputeClusterConflict(
                    f"A compute cluster with name '{self.name}' already exists."
                ),
            ),
        )

    @override
    def build_row(self) -> ComputeClusterRow:
        return ComputeClusterRow(
            name=self.name,
            description=self.description,
            api_server=self.api_server,
            kubeconfig=self.kubeconfig,
            namespace_prefix=self.namespace_prefix,
            gateway_addr=self.gateway_addr,
            gateway_public_key=self.gateway_public_key,
        )

    @override
    def to_data(self, row: ComputeClusterRow) -> ComputeClusterData:
        return ComputeClusterSearchableFields.own.to_data(row)
