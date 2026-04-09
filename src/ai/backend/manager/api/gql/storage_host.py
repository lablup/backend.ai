"""Storage host GraphQL types and resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.storage_host.response import (
    MyStorageHostPermissionsPayload,
    StorageHostPermissionNode,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import VFolderHostPermissionEnum
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A single storage host together with the permissions granted to a user.",
    ),
    model=StorageHostPermissionNode,
    name="StorageHostPermission",
)
class StorageHostPermissionGQL(PydanticOutputMixin[StorageHostPermissionNode]):
    """Storage host with the permissions the current user holds on it."""

    host: str = gql_field(description="Storage host name (e.g., 'local:volume1').")
    permissions: list[VFolderHostPermissionEnum] = gql_field(
        description="Permissions granted to the current user on this storage host.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload listing storage hosts the current user is allowed to use.",
    ),
    model=MyStorageHostPermissionsPayload,
    name="MyStorageHostPermissionsPayload",
)
class MyStorageHostPermissionsPayloadGQL(PydanticOutputMixin[MyStorageHostPermissionsPayload]):
    """List of storage hosts the current user can mount."""

    items: list[StorageHostPermissionGQL] = gql_field(
        description="Storage hosts the current user is allowed to use."
    )


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "List storage hosts the current user is allowed to mount, with the union "
            "of permissions inherited from domain, project, and keypair resource policies."
        ),
    )
)  # type: ignore[misc]
async def my_storage_host_permissions(
    info: Info[StrawberryGQLContext],
) -> MyStorageHostPermissionsPayloadGQL:
    payload = await info.context.adapters.storage_host.my_storage_host_permissions()
    return MyStorageHostPermissionsPayloadGQL.from_pydantic(payload)
