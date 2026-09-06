from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = ("ClientIPMaskingPolicySearcher",)


@dataclass
class ClientIPMaskingPolicySearcher(Searcher[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ClientIPMaskingPolicyRow)

    @override
    def to_data(self, row: ClientIPMaskingPolicyRow) -> ClientIPMaskingPolicyData:
        return row.to_data()
