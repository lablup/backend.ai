"""VFolder auto-mount GraphQL types."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Self, cast, override
from uuid import UUID

import strawberry
from strawberry import UNSET, Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    CreateVFolderAutoMountInput as CreateVFolderAutoMountInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    DeleteVFolderAutoMountInput as DeleteVFolderAutoMountInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    UpdateVFolderAutoMountInput as UpdateVFolderAutoMountInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    VFolderAutoMountFilter as VFolderAutoMountFilterDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    VFolderAutoMountOrder as VFolderAutoMountOrderDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    VFolderAutoMountPermissionFilter as VFolderAutoMountPermissionFilterDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    CreateVFolderAutoMountPayload as CreateVFolderAutoMountPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    DeleteVFolderAutoMountPayload as DeleteVFolderAutoMountPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    UpdateVFolderAutoMountPayload as UpdateVFolderAutoMountPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    VFolderAutoMountNode as VFolderAutoMountNodeDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.types import (
    VFolderAutoMountOrderField as VFolderAutoMountOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.types import (
    VFolderAutoMountScope as VFolderAutoMountScopeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    NullableDateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
    UUIDScopeGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.deployment.types.revision import MountPermission
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
    from ai.backend.manager.api.gql.vfolder_v2.types.node import VFolderGQL

__all__ = (
    "CreateVFolderAutoMountInputGQL",
    "CreateVFolderAutoMountPayloadGQL",
    "DeleteVFolderAutoMountInputGQL",
    "DeleteVFolderAutoMountPayloadGQL",
    "VFolderAutoMountConnectionGQL",
    "VFolderAutoMountEdgeGQL",
    "VFolderAutoMountFilterGQL",
    "VFolderAutoMountGQL",
    "VFolderAutoMountOrderByGQL",
    "VFolderAutoMountScopeGQL",
)


VFolderAutoMountOrderFieldGQL: type[VFolderAutoMountOrderFieldDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering vfolder auto-mounts.",
    ),
    VFolderAutoMountOrderFieldDTO,
    name="VFolderAutoMountOrderField",
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "A vfolder mounted into every session created in a project, a personal "
            "project included."
        ),
    ),
    name="VFolderAutoMount",
)
class VFolderAutoMountGQL(PydanticNodeMixin[VFolderAutoMountNodeDTO]):
    id: NodeID[str] = gql_field(description="Relay-style global node identifier.")
    entity_id: UUID = gql_field(description="ID of the auto-mount.")
    project_id: UUID = gql_field(description="ID of the project the vfolder is auto-mounted in.")
    vfolder_id: UUID = gql_field(description="ID of the auto-mounted vfolder.")
    mount_destination: str = gql_field(
        description="Path in the session container the vfolder is mounted at."
    )
    subpath: str = gql_field(description="Path inside the vfolder that is mounted.")
    mount_permission: MountPermission = gql_field(
        description="Permission the vfolder is mounted with."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")
    deleted_at: datetime | None = gql_field(
        description="Deletion timestamp. Null while the auto-mount is in use."
    )

    @gql_field(description="The project the vfolder is auto-mounted in.")  # type: ignore[misc]
    async def project(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            ProjectV2GQL,
            strawberry.lazy("ai.backend.manager.api.gql.project_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.project_loader.load(ProjectID(self.project_id))

    @gql_field(description="The auto-mounted vfolder.")  # type: ignore[misc]
    async def vfolder(
        self,
        info: Info[StrawberryGQLContext],
    ) -> (
        Annotated[
            VFolderGQL,
            strawberry.lazy("ai.backend.manager.api.gql.vfolder_v2.types.node"),
        ]
        | None
    ):
        return await info.context.data_loaders.vfolder_loader.load(VFolderUUID(self.vfolder_id))

    @classmethod
    @override
    async def resolve_nodes(
        cls,
        *,
        info: Info[StrawberryGQLContext, Any],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self]:
        results = await info.context.data_loaders.vfolder_auto_mount_loader.load_many([
            VFolderAutoMountID(UUID(node_id)) for node_id in node_ids
        ])
        return cast(list[Self], results)


VFolderAutoMountEdgeGQL = Edge[VFolderAutoMountGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Paginated connection for vfolder auto-mounts.",
    ),
    name="VFolderAutoMountConnection",
)
class VFolderAutoMountConnectionGQL(Connection[VFolderAutoMountGQL]):
    count: int = gql_field(description="Total number of auto-mounts matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Filter for the mount permission with equality and membership operators.",
    ),
    name="VFolderAutoMountPermissionFilter",
)
class VFolderAutoMountPermissionFilterGQL(PydanticInputMixin[VFolderAutoMountPermissionFilterDTO]):
    equals: MountPermission | None = gql_field(description="Exact match.", default=None)
    in_: list[MountPermission] | None = gql_field(
        description="Match any of the provided values.", name="in", default=None
    )
    not_equals: MountPermission | None = gql_field(
        description="Exclude an exact match.", default=None
    )
    not_in: list[MountPermission] | None = gql_field(
        description="Exclude any of the provided values.", default=None
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Filter for vfolder auto-mounts. Auto-mounts marked deleted are left out unless "
            "the top-level filter gives `deletedAt`; one inside AND, OR or NOT does not lift that."
        ),
    ),
    name="VFolderAutoMountFilter",
)
class VFolderAutoMountFilterGQL(PydanticInputMixin[VFolderAutoMountFilterDTO]):
    entity_id: UUIDFilter | None = gql_field(description="Filter by auto-mount ID.", default=None)
    project_id: UUIDFilter | None = gql_field(description="Filter by project ID.", default=None)
    vfolder_id: UUIDFilter | None = gql_field(description="Filter by vfolder ID.", default=None)
    mount_destination: StringFilter | None = gql_field(
        description="Filter by mount destination.", default=None
    )
    mount_permission: VFolderAutoMountPermissionFilterGQL | None = gql_field(
        description="Filter by mount permission.", default=None
    )
    created_at: DateTimeFilter | None = gql_field(
        description="Filter by creation time.", default=None
    )
    updated_at: DateTimeFilter | None = gql_field(
        description="Filter by last update time.", default=None
    )
    deleted_at: NullableDateTimeFilter | None = gql_field(
        description=(
            "Filter by deletion time. Setting it on the top-level filter includes the "
            "auto-mounts marked deleted; inside AND, OR or NOT it does not."
        ),
        default=None,
    )
    AND: list[Self] | None = gql_field(description="Match all nested filters.", default=None)
    OR: list[Self] | None = gql_field(description="Match any nested filter.", default=None)
    NOT: list[Self] | None = gql_field(description="Negate nested filters.", default=None)


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One ordering rule for a vfolder auto-mount search.",
    ),
    name="VFolderAutoMountOrderBy",
)
class VFolderAutoMountOrderByGQL(PydanticInputMixin[VFolderAutoMountOrderDTO]):
    field: VFolderAutoMountOrderFieldGQL = gql_field(description="Field to order by.")
    direction: OrderDirection = gql_field(
        description="Order direction.", default=OrderDirection.ASC
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Scope for the scoped vfolder auto-mount query. The items are OR'd, and every "
            "scope named is authorized before the read runs."
        ),
    ),
    name="VFolderAutoMountScope",
)
class VFolderAutoMountScopeGQL(PydanticInputMixin[VFolderAutoMountScopeDTO]):
    project: list[UUIDScopeGQL] = gql_field(
        description="Projects whose auto-mounts are being read. A personal project included."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for auto-mounting a vfolder into every session created in a project. The "
            "vfolder must belong to that project."
        ),
    ),
    name="CreateVFolderAutoMountInput",
)
class CreateVFolderAutoMountInputGQL(PydanticInputMixin[CreateVFolderAutoMountInputDTO]):
    project_id: UUID = gql_field(description="ID of the project the vfolder is auto-mounted in.")
    vfolder_id: UUID = gql_field(description="ID of the vfolder to auto-mount.")
    mount_destination: str = gql_field(
        description="Path in the session container the vfolder is mounted at."
    )
    subpath: str = gql_field(description="Path inside the vfolder that is mounted.", default=".")
    mount_permission: MountPermission = gql_field(
        description="Permission the vfolder is mounted with."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a vfolder auto-mount creation.",
    ),
    model=CreateVFolderAutoMountPayloadDTO,
    name="CreateVFolderAutoMountPayload",
)
class CreateVFolderAutoMountPayloadGQL(PydanticOutputMixin[CreateVFolderAutoMountPayloadDTO]):
    vfolder_auto_mount: VFolderAutoMountGQL = gql_field(description="The created auto-mount.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Input for changing where and how an auto-mounted vfolder is mounted. At least one "
            "of the three fields must be given."
        ),
    ),
    name="UpdateVFolderAutoMountInput",
)
class UpdateVFolderAutoMountInputGQL(PydanticInputMixin[UpdateVFolderAutoMountInputDTO]):
    id: UUID = gql_field(description="ID of the auto-mount to update.")
    mount_destination: str | None = gql_field(
        description="New path in the session container. Omit to leave unchanged.", default=UNSET
    )
    subpath: str | None = gql_field(
        description="New path inside the vfolder. Omit to leave unchanged.", default=UNSET
    )
    mount_permission: MountPermission | None = gql_field(
        description="New mount permission. Omit to leave unchanged.", default=UNSET
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a vfolder auto-mount update.",
    ),
    model=UpdateVFolderAutoMountPayloadDTO,
    name="UpdateVFolderAutoMountPayload",
)
class UpdateVFolderAutoMountPayloadGQL(PydanticOutputMixin[UpdateVFolderAutoMountPayloadDTO]):
    vfolder_auto_mount: VFolderAutoMountGQL = gql_field(description="The updated auto-mount.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Identifies the vfolder auto-mount to delete.",
    ),
    name="DeleteVFolderAutoMountInput",
)
class DeleteVFolderAutoMountInputGQL(PydanticInputMixin[DeleteVFolderAutoMountInputDTO]):
    id: UUID = gql_field(description="ID of the auto-mount to delete.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for a vfolder auto-mount deletion.",
    ),
    model=DeleteVFolderAutoMountPayloadDTO,
    name="DeleteVFolderAutoMountPayload",
)
class DeleteVFolderAutoMountPayloadGQL(PydanticOutputMixin[DeleteVFolderAutoMountPayloadDTO]):
    vfolder_auto_mount: VFolderAutoMountGQL = gql_field(
        description="The auto-mount marked deleted."
    )
