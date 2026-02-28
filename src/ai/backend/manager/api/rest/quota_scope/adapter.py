from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.dto.manager.quota_scope import QuotaScopeDTO
from ai.backend.manager.api.adapter import BaseFilterAdapter

__all__ = ("QuotaScopeAdapter",)


class QuotaScopeAdapter(BaseFilterAdapter):
    def convert_to_dto(
        self,
        quota_scope_id: str,
        storage_host_name: str,
        quota_config: Mapping[str, Any],
    ) -> QuotaScopeDTO:
        usage_bytes = quota_config.get("used_bytes")
        if usage_bytes is not None and usage_bytes < 0:
            usage_bytes = None
        return QuotaScopeDTO(
            quota_scope_id=quota_scope_id,
            storage_host_name=storage_host_name,
            usage_bytes=usage_bytes,
            usage_count=None,
            hard_limit_bytes=quota_config.get("limit_bytes") or None,
        )
