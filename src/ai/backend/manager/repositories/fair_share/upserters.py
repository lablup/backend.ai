"""Upserter specs for Fair Share repository upsert (INSERT ON CONFLICT UPDATE) operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.repositories.base import UpserterSpec


@dataclass
class DomainFairShareBulkWeightUpserterSpec(UpserterSpec[DomainFairShareRow]):
    """Simplified upserter spec for bulk weight updates on DomainFairShareRow.

    Used with BulkUpserter for updating weights across multiple domains.
    Has fixed update column (weight only) to ensure consistent bulk operations.
    """

    resource_group: str
    resource_group_id: ResourceGroupID
    domain_name: str
    weight: Decimal | None  # None means use resource group's default_weight

    @property
    @override
    def row_class(self) -> type[DomainFairShareRow]:
        return DomainFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "resource_group": self.resource_group,
            "resource_group_id": self.resource_group_id,
            "domain_name": self.domain_name,
            "weight": self.weight,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"resource_group_id": self.resource_group_id, "weight": self.weight}


@dataclass
class ProjectFairShareBulkWeightUpserterSpec(UpserterSpec[ProjectFairShareRow]):
    """Simplified upserter spec for bulk weight updates on ProjectFairShareRow.

    Used with BulkUpserter for updating weights across multiple projects.
    Has fixed update column (weight only) to ensure consistent bulk operations.
    """

    resource_group: str
    resource_group_id: ResourceGroupID
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None  # None means use resource group's default_weight

    @property
    @override
    def row_class(self) -> type[ProjectFairShareRow]:
        return ProjectFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "resource_group": self.resource_group,
            "resource_group_id": self.resource_group_id,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
            "weight": self.weight,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"resource_group_id": self.resource_group_id, "weight": self.weight}


@dataclass
class UserFairShareBulkWeightUpserterSpec(UpserterSpec[UserFairShareRow]):
    """Simplified upserter spec for bulk weight updates on UserFairShareRow.

    Used with BulkUpserter for updating weights across multiple users.
    Has fixed update column (weight only) to ensure consistent bulk operations.
    """

    resource_group: str
    resource_group_id: ResourceGroupID
    user_uuid: uuid.UUID
    project_id: uuid.UUID
    domain_name: str
    weight: Decimal | None  # None means use resource group's default_weight

    @property
    @override
    def row_class(self) -> type[UserFairShareRow]:
        return UserFairShareRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "resource_group": self.resource_group,
            "resource_group_id": self.resource_group_id,
            "user_uuid": self.user_uuid,
            "project_id": self.project_id,
            "domain_name": self.domain_name,
            "weight": self.weight,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"resource_group_id": self.resource_group_id, "weight": self.weight}
