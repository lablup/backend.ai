"""Delete specs for the keypairs table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.conditions import KeypairConditions
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.purger import GuardedFieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class NonDefaultKeypairPurger(GuardedFieldPurger[KeyPairRow, KeyPairData]):
    """Removes one keypair, leaving the key its user authorizes with alone.

    The guard rides on the statement: a key that becomes the default while the delete
    runs is filtered out on re-evaluation, so nothing is removed.
    """

    keypair_id: KeyPairID

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
        return [KeypairConditions.by_is_default(False)]

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()
