"""Common Resource Usage GQL types."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

import strawberry


@strawberry.type(
    name="UsageBucketMetadata",
    description=(
        "Added in 26.1.0. Common metadata for usage bucket records including "
        "the measurement period and timestamps."
    ),
)
class UsageBucketMetadataGQL:
    """Common metadata for usage bucket records."""

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
