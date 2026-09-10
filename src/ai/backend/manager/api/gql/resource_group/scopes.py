"""Resource group GraphQL scope types.

Kept out of ``types.py``: the scope item type lives under ``rbac``, whose package
reaches back here for :class:`ResourceGroupGQL`.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.resource_group.types import ResourceGroupScope
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
