"""VFolder GraphQL scope types."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.vfolder.types import VFolderScope, VFolderUsedBy
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Entities whose use narrows a vfolder query; every id is AND-ed. The caller must "
            "be able to read each listed entity, or the request is refused. Only vfolders the "
            "caller can read are returned, even when a listed entity uses others."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="VFolderUsedBy",
)
class VFolderUsedByGQL(PydanticInputMixin[VFolderUsedBy]):
    """The entities whose use of a vfolder narrows the read."""

    deployment: list[UUID] | None = gql_field(
        default=None,
        description="Deployments whose live replica groups use the vfolder as the model of their current revision.",
    )
    model_card: list[UUID] | None = gql_field(
        default=None, description="Model cards built on the vfolder."
    )
