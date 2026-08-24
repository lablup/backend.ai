from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.client_ip_masking import ClientIPMaskingPolicyID
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier

from .masking import ClientIPMaskingMode, ClientIPMaskingTarget


@dataclass(frozen=True)
class ClientIPMaskingPolicyData(EntityData):
    id: ClientIPMaskingPolicyID
    target_type: ClientIPMaskingTarget
    mode: ClientIPMaskingMode
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id
