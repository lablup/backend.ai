"""GraphQL types for deployment options (timeouts, etc.).

Mirrors the shared :mod:`ai.backend.common.dto.manager.v2.deployment_options`
DTOs so both input (Replace mutations) and output (``DeploymentNode.options``)
surfaces can travel through GraphQL with Strawberry-compatible types.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentOptionsInput as DeploymentOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentTimeoutsInput as DeploymentTimeoutsInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.request import (
    HandlerTimeoutEntryInput as HandlerTimeoutEntryInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.response import (
    DeploymentOptionsInfo as DeploymentOptionsInfoDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.response import (
    DeploymentTimeoutsInfo as DeploymentTimeoutsInfoDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.response import (
    HandlerTimeoutEntryInfo as HandlerTimeoutEntryInfoDTO,
)
from ai.backend.common.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_pydantic_input,
    gql_pydantic_type,
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A single (handler_name, timeout_sec) entry.",
    ),
    name="HandlerTimeoutEntryInput",
)
class HandlerTimeoutEntryInputGQL(PydanticInputMixin[HandlerTimeoutEntryInputDTO]):
    handler_name: str
    timeout_sec: int | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Deployment timeout policy input.",
    ),
    name="DeploymentTimeoutsInput",
)
class DeploymentTimeoutsInputGQL(PydanticInputMixin[DeploymentTimeoutsInputDTO]):
    default: int | None = None
    by_handler: list[HandlerTimeoutEntryInputGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Deployment options payload input.",
    ),
    name="DeploymentOptionsInput",
)
class DeploymentOptionsInputGQL(PydanticInputMixin[DeploymentOptionsInputDTO]):
    timeouts: DeploymentTimeoutsInputGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A single (handler_name, timeout_sec) entry response.",
    ),
    model=HandlerTimeoutEntryInfoDTO,
)
class HandlerTimeoutEntryInfoGQL:
    handler_name: str
    timeout_sec: int | None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Deployment timeout policy response.",
    ),
    model=DeploymentTimeoutsInfoDTO,
)
class DeploymentTimeoutsInfoGQL:
    default: int | None
    by_handler: list[HandlerTimeoutEntryInfoGQL]


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Deployment options payload response.",
    ),
    model=DeploymentOptionsInfoDTO,
)
class DeploymentOptionsInfoGQL:
    timeouts: DeploymentTimeoutsInfoGQL
