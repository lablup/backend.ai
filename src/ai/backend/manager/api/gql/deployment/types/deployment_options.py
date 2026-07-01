"""GraphQL types for deployment options (handler options, etc.).

Mirrors the shared :mod:`ai.backend.common.dto.manager.v2.deployment_options`
DTOs so both input (Replace mutations) and output (``DeploymentNode.options``)
surfaces can travel through GraphQL with Strawberry-compatible types.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentHandlerOptionsInput as DeploymentHandlerOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentOptionsInput as DeploymentOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.response import (
    DeploymentHandlerOptionsInfo as DeploymentHandlerOptionsInfoDTO,
)
from ai.backend.common.dto.manager.v2.deployment_options.response import (
    DeploymentOptionsInfo as DeploymentOptionsInfoDTO,
)
from ai.backend.common.dto.manager.v2.session_options.request import (
    HandlerOptionsEntryInput as HandlerOptionsEntryInputDTO,
)
from ai.backend.common.dto.manager.v2.session_options.request import (
    HandlerOptionsInput as HandlerOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.session_options.response import (
    HandlerOptionsEntryInfo as HandlerOptionsEntryInfoDTO,
)
from ai.backend.common.dto.manager.v2.session_options.response import (
    HandlerOptionsInfo as HandlerOptionsInfoDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_pydantic_input,
    gql_pydantic_type,
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Per-handler scheduler policy fields for deployment handler options.",
    ),
    name="HandlerOptionsInput",
)
class HandlerOptionsInputGQL(PydanticInputMixin[HandlerOptionsInputDTO]):
    timeout_sec: int | None = None
    max_retry_count: int | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="A single (handler_name, options) entry for deployment handler options.",
    ),
    name="HandlerOptionsEntryInput",
)
class HandlerOptionsEntryInputGQL(PydanticInputMixin[HandlerOptionsEntryInputDTO]):
    handler_name: str
    timeout_sec: int | None = None
    max_retry_count: int | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Deployment handler-options policy input.",
    ),
    name="DeploymentHandlerOptionsInput",
)
class DeploymentHandlerOptionsInputGQL(PydanticInputMixin[DeploymentHandlerOptionsInputDTO]):
    default: HandlerOptionsInputGQL | None = None
    by_handler: list[HandlerOptionsEntryInputGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Deployment options payload input.",
    ),
    name="DeploymentOptionsInput",
)
class DeploymentOptionsInputGQL(PydanticInputMixin[DeploymentOptionsInputDTO]):
    handler_options: DeploymentHandlerOptionsInputGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Per-handler scheduler policy snapshot for deployment handler options.",
    ),
    model=HandlerOptionsInfoDTO,
    name="HandlerOptionsInfo",
)
class HandlerOptionsInfoGQL:
    timeout_sec: int | None
    max_retry_count: int | None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="A single (handler_name, options) entry response for deployment handler options.",
    ),
    model=HandlerOptionsEntryInfoDTO,
    name="HandlerOptionsEntryInfo",
)
class HandlerOptionsEntryInfoGQL:
    handler_name: str
    timeout_sec: int | None
    max_retry_count: int | None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Deployment handler-options policy response.",
    ),
    model=DeploymentHandlerOptionsInfoDTO,
    name="DeploymentHandlerOptionsInfo",
)
class DeploymentHandlerOptionsInfoGQL:
    default: HandlerOptionsInfoGQL
    by_handler: list[HandlerOptionsEntryInfoGQL]


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Deployment options payload response.",
    ),
    model=DeploymentOptionsInfoDTO,
    name="DeploymentOptionsInfo",
)
class DeploymentOptionsInfoGQL:
    handler_options: DeploymentHandlerOptionsInfoGQL
