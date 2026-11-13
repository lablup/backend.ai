"""Group inputs shared by the aggregate queries, one per value type."""

from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "DateTimeGroup",
    "EnumGroup",
    "StringGroup",
    "UUIDGroup",
)


class EnumGroup(BaseRequestModel):
    """Group by an enum field."""

    include_empty: bool = Field(
        default=False, description="Also return the enum values no row has, with a zero count."
    )


class DateTimeGroup(BaseRequestModel):
    """Group by a datetime field into half-open buckets ``[start, end)`` of a fixed length.

    Buckets are aligned to midnight in ``timezone``, and weeks to Monday. The filter sets the range.
    """

    interval_seconds: int = Field(ge=1, description="Bucket length in seconds.")
    timezone: str | None = Field(
        default=None, description="IANA time zone the buckets align to. UTC when omitted."
    )

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(f"Unknown time zone: {value}") from e
        return value


class UUIDGroup(BaseRequestModel):
    """Group by a UUID field."""

    include_null: bool = Field(
        default=False, description="Return the rows with no value as one group."
    )


class StringGroup(BaseRequestModel):
    """Group by a string field."""

    include_null: bool = Field(
        default=False, description="Return the rows with no value as one group."
    )
