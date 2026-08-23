"""Update specs for the keypairs table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.errors.keypair import KeypairResourcePolicyNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.conditions import KeypairConditions
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater, GuardedDataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class KeypairDotfilesUpdater(DataUpdater[KeyPairRow, KeyPairData]):
    """Replaces the packed dotfile entries a keypair hands to its sessions."""

    keypair_id: KeyPairID
    dotfiles: bytes

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.keypair_id

    @override
    def build_values(self) -> dict[str, Any]:
        return {"dotfiles": self.dotfiles}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()


@dataclass
class KeypairBootstrapScriptUpdater(DataUpdater[KeyPairRow, KeyPairData]):
    """Replaces the bootstrap script a keypair carries."""

    keypair_id: KeyPairID
    script: str

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.keypair_id

    @override
    def build_values(self) -> dict[str, Any]:
        return {"bootstrap_script": self.script}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()


@dataclass
class KeypairUpdater(GuardedDataUpdater[KeyPairRow, KeyPairData]):
    """Writes a keypair's settings, declining to deactivate the key its user
    authorizes with.

    Login reads the default marker alone, so an inactive default locks the user out —
    the same rule the delete keeps. The guard rides on the statement and is carried
    only by a write that clears ``is_active``.
    """

    keypair_id: KeyPairID
    is_active: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    is_admin: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    rate_limit: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.keypair_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        if self.is_active.optional_value() is not False:
            return []
        return [KeypairConditions.by_is_default(False)]

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.is_active.update_dict(to_update, "is_active")
        self.is_admin.update_dict(to_update, "is_admin")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.rate_limit.update_dict(to_update, "rate_limit")
        return to_update

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        policy = self.resource_policy.optional_value()
        if policy is None:
            return ()
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_keypairs_resource_policy_keypair_resource_policies",
                error=KeypairResourcePolicyNotFound(policy),
            ),
        )

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()
