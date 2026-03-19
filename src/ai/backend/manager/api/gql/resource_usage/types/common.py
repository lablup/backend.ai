"""Common Resource Usage GQL types."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

import strawberry

from ai.backend.common.dto.manager.v2.resource_usage.response import (
    UsageBucketMetadataNode as UsageBucketMetadataNodeDTO,
)


@strawberry.experimental.pydantic.type(
    model=UsageBucketMetadataNodeDTO,
    name="UsageBucketMetadata",
    description=(
        "Added in 26.1.0. Common metadata for usage bucket records including "
        "the measurement period and timestamps."
    ),
    all_fields=True,
)
class UsageBucketMetadataGQL:
    period_start: date
    period_end: date
    decay_unit_days: int
    created_at: datetime
    updated_at: datetime


@strawberry.enum(
    name="UsageBucketOrderField",
    description=(
        "Added in 26.1.0. Fields available for ordering usage bucket query results. "
        "PERIOD_START: Order by the start date of the usage measurement period. "
        "Use DESC to get most recent buckets first, ASC for chronological order."
    ),
)
class UsageBucketOrderField(StrEnum):
    PERIOD_START = "period_start"
