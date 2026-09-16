"""VFolder GraphQL scope types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.vfolder.types import VFolderScope
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
            "Scope for the scoped vfolder query. Each list is OR'd internally and "
            "across lists, and every scope named is authorized before the read runs."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderScope",
)
class VFolderScopeGQL(PydanticInputMixin[VFolderScope]):
    """The scopes a vfolder read is answered for."""

    domain: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Domains whose vfolders are being read."
    )
    project: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Projects whose vfolders are being read."
    )
    user: list[UUIDScopeGQL] | None = gql_field(
        default=None, description="Users whose vfolders are being read."
    )
