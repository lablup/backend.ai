"""Common Resource Usage GQL types."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from ai.backend.common.dto.manager.v2.resource_usage.response import (
    UsageBucketMetadataNode as UsageBucketMetadataNodeDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Common metadata for usage bucket records including "
            "the measurement period and timestamps."
        ),
    ),
    model=UsageBucketMetadataNodeDTO,
    name="UsageBucketMetadata",
)
class UsageBucketMetadataGQL(PydanticOutputMixin[UsageBucketMetadataNodeDTO]):
    period_start: date = gql_field(
        description="Start date of the usage measurement period (inclusive)."
    )
    period_end: date = gql_field(
        description="End date of the usage measurement period (exclusive)."
    )
    decay_unit_days: int = gql_field(
        description="Number of days in each decay unit for this bucket."
    )
    created_at: datetime = gql_field(description="Timestamp when this record was created.")
    updated_at: datetime = gql_field(description="Timestamp when this record was last updated.")


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.1.0",
        description=(
            "Fields available for ordering usage bucket query results. "
            "PERIOD_START: Order by the start date of the usage measurement period. "
            "Use DESC to get most recent buckets first, ASC for chronological order."
        ),
    ),
    name="UsageBucketOrderField",
)
class UsageBucketOrderField(StrEnum):
    PERIOD_START = "period_start"
