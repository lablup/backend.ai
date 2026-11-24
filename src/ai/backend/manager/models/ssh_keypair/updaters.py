"""Update specs for SSH keys."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.ssh_keypair import DefaultSSHKeyConflict
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.ssh_keypair.searchable_fields import SSHKeypairSearchableFields

__all__ = (
    "SSHKeyDefaultClearUpdater",
    "SSHKeyDefaultSetUpdater",
)


@dataclass
class SSHKeyDefaultClearUpdater(DataBatchUpdater[SSHKeypairRow, SSHKeypairData]):
    """Unmark the default SSH key of the users the scope names."""

    @property
    @override
    def row_class(self) -> type[SSHKeypairRow]:
        return SSHKeypairRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [SSHKeypairSearchableFields.own.is_default.filter.equals(True)]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": False}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairSearchableFields.own.to_data(row)


@dataclass
class SSHKeyDefaultSetUpdater(DataUpdater[SSHKeypairRow, SSHKeypairData]):
    """Mark one SSH key as its user's default."""

    ssh_key_id: SSHKeypairID

    @property
    @override
    def row_class(self) -> type[SSHKeypairRow]:
        return SSHKeypairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SSHKeypairRow.id

    @override
    def target_id_value(self) -> SSHKeypairID:
        return self.ssh_key_id

    @override
    def build_values(self) -> dict[str, Any]:
        return {"is_default": True}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_ssh_keypairs_is_default",
                error=DefaultSSHKeyConflict(),
            ),
        )

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairSearchableFields.own.to_data(row)
