"""Container Registry V2 GraphQL filter and order types."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.container_registry.request import (
    ContainerRegistryFilter as ContainerRegistryFilterDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.request import (
    ContainerRegistryOrder as ContainerRegistryOrderDTO,
)
from ai.backend.common.dto.manager.v2.container_registry.types import (
    ContainerRegistryTypeFilter as ContainerRegistryTypeFilterDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    OrderDirection,
    StringFilter,
)
from ai.backend.manager.api.gql.container_registry.types import ContainerRegistryTypeGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter by container registry type.",
    ),
    name="ContainerRegistryTypeFilter",
)
class ContainerRegistryTypeFilterGQL(PydanticInputMixin[ContainerRegistryTypeFilterDTO]):
    equals: ContainerRegistryTypeGQL | None = None
    not_equals: ContainerRegistryTypeGQL | None = None
    in_: list[ContainerRegistryTypeGQL] | None = None
    not_in: list[ContainerRegistryTypeGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for container registries.",
    ),
    name="ContainerRegistryV2Filter",
)
class ContainerRegistryV2Filter(PydanticInputMixin[ContainerRegistryFilterDTO]):
    registry_name: StringFilter | None = None
    type: ContainerRegistryTypeFilterGQL | None = None
    is_global: bool | None = None


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering container registries.",
    ),
    name="ContainerRegistryV2OrderField",
)
class ContainerRegistryV2OrderField(StrEnum):
    REGISTRY_NAME = "registry_name"
    URL = "url"
    TYPE = "type"
    IS_GLOBAL = "is_global"


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Ordering specification for container registries.",
    ),
    name="ContainerRegistryV2OrderBy",
)
class ContainerRegistryV2OrderBy(PydanticInputMixin[ContainerRegistryOrderDTO]):
    field: ContainerRegistryV2OrderField = gql_field(
        default=ContainerRegistryV2OrderField.REGISTRY_NAME, description="Field to order by."
    )
    direction: OrderDirection = gql_field(default=OrderDirection.ASC, description="Sort direction.")
