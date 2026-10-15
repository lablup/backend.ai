"""Read specs for the client IP masking policies table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.client_ip_masking.searchable_fields import (
    ClientIPMaskingPolicySearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkClientIPMaskingPolicyQuerier(
    BulkEntityQuerier[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """The client IP masking policies the caller named."""

    @override
    def row_class(self) -> type[ClientIPMaskingPolicyRow]:
        return ClientIPMaskingPolicyRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ClientIPMaskingPolicyRow.id

    @override
    def to_data(self, row: ClientIPMaskingPolicyRow) -> ClientIPMaskingPolicyData:
        return ClientIPMaskingPolicySearchableFields.own.to_data(row)
