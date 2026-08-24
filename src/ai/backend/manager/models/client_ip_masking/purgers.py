from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck

__all__ = ("ClientIPMaskingPolicyPurger",)


@dataclass
class ClientIPMaskingPolicyPurger(
    EntityPurger[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Drop one target's policy so it falls back to ``default``."""

    policy_id: ClientIPMaskingPolicyID

    @override
    def row_class(self) -> type[ClientIPMaskingPolicyRow]:
        return ClientIPMaskingPolicyRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ClientIPMaskingPolicyRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ClientIPMaskingPolicyRow) -> ClientIPMaskingPolicyData:
        return row.to_data()
