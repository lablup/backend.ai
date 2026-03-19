"""Common Resource Usage GQL types."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Self

import strawberry

from ai.backend.common.dto.manager.v2.resource_usage.response import (
    UsageBucketMetadataNode as UsageBucketMetadataNodeDTO,
)
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_node_type


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Common metadata for usage bucket records including "
            "the measurement period and timestamps."
        ),
    ),
    name="UsageBucketMetadata",
)
class UsageBucketMetadataGQL:
    period_start: date = strawberry.field(
        description="Start date of the usage measurement period (inclusive)."
    )
    period_end: date = strawberry.field(
        description="End date of the usage measurement period (exclusive)."
    )
    decay_unit_days: int = strawberry.field(
        description="Number of days in each decay unit for this bucket."
    )
    created_at: datetime = strawberry.field(description="Timestamp when this record was created.")
    updated_at: datetime = strawberry.field(
        description="Timestamp when this record was last updated."
    )

    @classmethod
    def from_pydantic(cls, dto: UsageBucketMetadataNodeDTO) -> Self:
        return cls(
            period_start=dto.period_start,
            period_end=dto.period_end,
            decay_unit_days=dto.decay_unit_days,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


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
