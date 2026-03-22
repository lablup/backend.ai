"""Prometheus query preset GQL input types."""

from __future__ import annotations

from datetime import datetime

import strawberry
from strawberry import UNSET

from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput as CreateQueryDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionOptionsInput as CreateQueryDefinitionOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ExecuteQueryDefinitionOptionsInput as ExecuteQueryDefinitionOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    MetricLabelEntry as MetricLabelEntryDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ModifyQueryDefinitionInput as ModifyQueryDefinitionInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ModifyQueryDefinitionOptionsInput as ModifyQueryDefinitionOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    QueryTimeRangeInputDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(description="Options for query definition labels.", added_version="26.3.0"),
    name="QueryDefinitionOptionsInput",
)
class QueryDefinitionOptionsInput(PydanticInputMixin[CreateQueryDefinitionOptionsInputDTO]):
    filter_labels: list[str] = strawberry.field(description="Allowed filter label keys.")
    group_labels: list[str] = strawberry.field(description="Allowed group-by label keys.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a new query definition.", added_version="26.3.0"
    ),
    name="CreateQueryDefinitionInput",
)
class CreateQueryDefinitionInput(PydanticInputMixin[CreateQueryDefinitionInputDTO]):
    name: str = strawberry.field(description="Human-readable identifier (must be unique).")
    metric_name: str = strawberry.field(description="Prometheus metric name.")
    query_template: str = strawberry.field(
        description="PromQL template with {labels}, {window}, {group_by} placeholders."
    )
    time_window: str | None = strawberry.field(default=None, description="Default time window.")
    options: QueryDefinitionOptionsInput = strawberry.field(
        description="Query definition options including filter and group labels."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Options for modifying an existing query definition.", added_version="26.3.0"
    ),
    name="ModifyQueryDefinitionOptionsInput",
)
class ModifyQueryDefinitionOptionsInputGQL(
    PydanticInputMixin[ModifyQueryDefinitionOptionsInputDTO]
):
    filter_labels: list[str] | None = strawberry.field(
        default=None, description="Allowed filter label keys."
    )
    group_labels: list[str] | None = strawberry.field(
        default=None, description="Allowed group-by label keys."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for modifying an existing query definition.", added_version="26.3.0"
    ),
    name="ModifyQueryDefinitionInput",
)
class ModifyQueryDefinitionInput(PydanticInputMixin[ModifyQueryDefinitionInputDTO]):
    name: str | None = strawberry.field(default=UNSET, description="New name.")
    metric_name: str | None = strawberry.field(default=UNSET, description="New metric name.")
    query_template: str | None = strawberry.field(default=UNSET, description="New PromQL template.")
    time_window: str | None = strawberry.field(
        default=UNSET, description="New default time window."
    )
    options: ModifyQueryDefinitionOptionsInputGQL | None = strawberry.field(
        default=UNSET, description="New query definition options."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(description="Time range for Prometheus query.", added_version="26.3.0"),
    name="QueryTimeRangeInput",
)
class QueryTimeRangeInput(PydanticInputMixin[QueryTimeRangeInputDTO]):
    start: datetime = strawberry.field(description="Start of the time range.")
    end: datetime = strawberry.field(description="End of the time range.")
    step: str = strawberry.field(description="Query resolution step (e.g., '60s').")


@gql_pydantic_input(
    BackendAIGQLMeta(description="Key-value label entry for queries.", added_version="26.3.0"),
    name="MetricLabelEntryInput",
)
class MetricLabelEntryInput(PydanticInputMixin[MetricLabelEntryDTO]):
    key: str = strawberry.field(description="Label key.")
    value: str = strawberry.field(description="Label value.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Options for executing a query definition.", added_version="26.3.0"
    ),
    name="ExecuteQueryDefinitionOptionsInput",
)
class ExecuteQueryDefinitionOptionsInput(PydanticInputMixin[ExecuteQueryDefinitionOptionsInputDTO]):
    filter_labels: list[MetricLabelEntryInput] | None = strawberry.field(
        default=None, description="Label key-value pairs to filter by."
    )
    group_labels: list[str] | None = strawberry.field(
        default=None, description="Label keys to group results by."
    )
