"""What a client IP masking policy search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ClientIPMaskingPolicyOwnFields(
    RowDataConverter[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """The masking policy's own columns."""

    id = SearchableField(
        ClientIPMaskingPolicyRow.id,
        UUIDConditions(ClientIPMaskingPolicyRow.id),
        ColumnOrder(ClientIPMaskingPolicyRow.id),
    )
    target_type = SearchableField(
        ClientIPMaskingPolicyRow.target_type,
        EnumConditions(ClientIPMaskingPolicyRow.target_type, ClientIPMaskingTarget),
        ColumnOrder(ClientIPMaskingPolicyRow.target_type),
    )
    mode = SearchableField(
        ClientIPMaskingPolicyRow.mode,
        EnumConditions(ClientIPMaskingPolicyRow.mode, ClientIPMaskingMode),
        ColumnOrder(ClientIPMaskingPolicyRow.mode),
    )
    ipv4_prefix = SearchableField(
        ClientIPMaskingPolicyRow.ipv4_prefix,
        IntConditions(ClientIPMaskingPolicyRow.ipv4_prefix),
        ColumnOrder(ClientIPMaskingPolicyRow.ipv4_prefix),
    )
    ipv6_prefix = SearchableField(
        ClientIPMaskingPolicyRow.ipv6_prefix,
        IntConditions(ClientIPMaskingPolicyRow.ipv6_prefix),
        ColumnOrder(ClientIPMaskingPolicyRow.ipv6_prefix),
    )
    created_at = SearchableField(
        ClientIPMaskingPolicyRow.created_at,
        DateTimeConditions(ClientIPMaskingPolicyRow.created_at),
        ColumnOrder(ClientIPMaskingPolicyRow.created_at),
    )
    updated_at = SearchableField(
        ClientIPMaskingPolicyRow.updated_at,
        DateTimeConditions(ClientIPMaskingPolicyRow.updated_at),
        ColumnOrder(ClientIPMaskingPolicyRow.updated_at),
    )

    @override
    def to_data(self, row: ClientIPMaskingPolicyRow) -> ClientIPMaskingPolicyData:
        return ClientIPMaskingPolicyData(
            id=ClientIPMaskingPolicyID(self.id.read(row)),
            target_type=self.target_type.read(row),
            mode=self.mode.read(row),
            ipv4_prefix=self.ipv4_prefix.read(row),
            ipv6_prefix=self.ipv6_prefix.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class ClientIPMaskingPolicySearchableFields:
    own = _ClientIPMaskingPolicyOwnFields()
