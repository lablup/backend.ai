"""Upsert specs for the domains table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import ResourceSlot, VFolderHostPermission
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.domain.searchable_fields import DomainSearchableFields
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("DomainUpserter",)


@dataclass
class DomainUpserter(CreatedInGlobal[DomainRow], EntityUpserter[DomainRow, DomainData]):
    """Write a domain under its stated id.

    Conflict key: id. ``name`` is written on insert only: users and projects refer to the
    domain by it. ``status``, ``integration_id`` and ``dotfiles`` are left as they are.
    """

    id: DomainID
    name: str
    description: str | None
    is_active: bool
    is_default: bool
    total_resource_slots: ResourceSlot
    allowed_vfolder_hosts: dict[str, list[VFolderHostPermission]]
    allowed_docker_registries: list[str]

    @override
    def entity_id(self, row: DomainRow) -> DomainID:
        return DomainID(row.id)

    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "total_resource_slots": self.total_resource_slots,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "allowed_docker_registries": self.allowed_docker_registries,
        }

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return DomainSearchableFields.own.to_data(row)
