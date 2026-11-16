"""Values shared by the aggregate results."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AggregateValueInfo",
    "DateTimeBucketInfo",
)


class AggregateValueInfo(BaseResponseModel):
    count: int = Field(description="Number of rows.")


class DateTimeBucketInfo(BaseResponseModel):
    """The half-open range ``[start, end)`` of one datetime group."""

    start: datetime = Field(description="Start of the bucket, inclusive.")
    end: datetime = Field(description="End of the bucket, exclusive.")
