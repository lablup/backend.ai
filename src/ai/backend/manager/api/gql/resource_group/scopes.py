"""Resource group GraphQL scope types.

Kept out of ``types.py``: the scope item type lives under ``rbac``, whose package
reaches back here for :class:`ResourceGroupGQL`.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupScope,
    ResourceGroupUsage,
    ResourceGroupUsedBy,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import UUIDScopeGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Scope for the scoped resource group query. Each list is OR'd internally and "
            "across lists, and every scope named is authorized before the read runs."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="ResourceGroupScope",
)
class ResourceGroupScopeGQL(PydanticInputMixin[ResourceGroupScope]):
    """The scopes a resource group read is answered for."""

    domain: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Domains whose resource groups are being read."
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects whose resource groups are being read."
    )
    user: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users whose resource groups are being read."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Entities whose use of a resource group narrows the read.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="ResourceGroupUsedBy",
)
class ResourceGroupUsedByGQL(PydanticInputMixin[ResourceGroupUsedBy]):
    """The entities whose use of a resource group narrows the read."""

    session: list[UUID] | None = gql_field(
        default=None, description="Sessions the resource group runs."
    )
    deployment: list[UUID] | None = gql_field(
        default=None, description="Deployments the resource group runs."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Uses narrowing a resource group query; every id is AND-ed. The caller must be "
            "able to read each listed entity, or the request is refused. Only resource groups "
            "the caller can read are returned, even when a listed entity is tied to others."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="ResourceGroupUsage",
)
class ResourceGroupUsageGQL(PydanticInputMixin[ResourceGroupUsage]):
    """The uses that narrow a resource group read."""

    used_by: ResourceGroupUsedByGQL | None = gql_field(
        default=None, description="Entities whose use of the resource group narrows the read."
    )
