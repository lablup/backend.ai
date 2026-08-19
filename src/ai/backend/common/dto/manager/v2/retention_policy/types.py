from __future__ import annotations

from enum import StrEnum

from ai.backend.common.data.retention.types import RetentionCategory

__all__ = ("RetentionCategory", "RetentionPolicyOrderField")


class RetentionPolicyOrderField(StrEnum):
    CATEGORY = "category"
    CREATED_AT = "created_at"
    LAST_SWEPT_AT = "last_swept_at"
