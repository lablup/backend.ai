"""Group inputs and result values shared by the aggregate queries."""

from __future__ import annotations

from datetime import datetime

from ai.backend.common.dto.manager.v2.aggregate.request import (
    DateTimeGroup,
    EnumGroup,
    StringGroup,
    UUIDGroup,
)
from ai.backend.common.dto.manager.v2.aggregate.response import (
    AggregateValueInfo,
    DateTimeBucketInfo,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(description="Group by an enum field.", added_version=NEXT_RELEASE_VERSION),
    name="EnumGroup",
)
class EnumGroupGQL(PydanticInputMixin[EnumGroup]):
    include_empty: bool = gql_field(
        description="Also return the enum values no row has, with a zero count.",
        default=False,
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Group by a datetime field into half-open buckets [start, end) of a fixed length, "
            "aligned to midnight in the time zone and to Monday for weeks. "
            "The filter sets the range."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="DateTimeGroup",
)
class DateTimeGroupGQL(PydanticInputMixin[DateTimeGroup]):
    interval_seconds: int = gql_field(description="Bucket length in seconds.")
    timezone: str | None = gql_field(
        description="IANA time zone the buckets align to. UTC when omitted.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Group by a UUID field.", added_version=NEXT_RELEASE_VERSION),
    name="UUIDGroup",
)
class UUIDGroupGQL(PydanticInputMixin[UUIDGroup]):
    include_null: bool = gql_field(
        description="Return the rows with no value as one group.", default=False
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Group by a string field.", added_version=NEXT_RELEASE_VERSION),
    name="StringGroup",
)
class StringGroupGQL(PydanticInputMixin[StringGroup]):
    include_null: bool = gql_field(
        description="Return the rows with no value as one group.", default=False
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="Aggregate values of a set of rows.", added_version=NEXT_RELEASE_VERSION
    ),
    model=AggregateValueInfo,
    name="AggregateValue",
)
class AggregateValueGQL:
    count: int = gql_field(description="Number of rows.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        description="The half-open range [start, end) of one datetime group.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    model=DateTimeBucketInfo,
    name="DateTimeBucket",
)
class DateTimeBucketGQL:
    start: datetime = gql_field(description="Start of the bucket, inclusive.")
    end: datetime = gql_field(description="End of the bucket, exclusive.")
