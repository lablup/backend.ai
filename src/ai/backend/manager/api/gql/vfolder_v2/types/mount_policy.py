"""GraphQL types for the mount level one user gets on a virtual folder."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ai.backend.common.dto.manager.v2.vfolder.request import (
    SetVFolderMountPolicyInput as SetInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.request import (
    UnsetVFolderMountPolicyInput as UnsetInputDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SetVFolderMountPolicyPayload as SetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    UnsetVFolderMountPolicyPayload as UnsetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderMountPoliciesPayload as ListPayloadDTO,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    VFolderMountPolicyNode as NodeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.vfolder_v2.types.enum import VFolderMountPermissionGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="The mount level one user gets on a virtual folder.",
    ),
    model=NodeDTO,
    name="VFolderMountPolicy",
)
class VFolderMountPolicyGQL(PydanticOutputMixin[NodeDTO]):
    id: UUID = gql_field(description="Mount policy row ID.")
    vfolder_id: UUID = gql_field(description="ID of the virtual folder.")
    user_id: UUID = gql_field(description="User the mount level is set for.")
    permission: VFolderMountPermissionGQL = gql_field(description="Mount level: NONE, RO or RW.")
    created_at: datetime = gql_field(description="When the row was first set.")
    updated_at: datetime = gql_field(description="When the level was last replaced.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for setting the mount level one user gets on a virtual folder.",
    ),
    name="SetVFolderMountPolicyInput",
)
class SetVFolderMountPolicyInputGQL(PydanticInputMixin[SetInputDTO]):
    user_id: UUID = gql_field(description="User the mount level is set for.")
    permission: VFolderMountPermissionGQL = gql_field(
        description="Mount level: NONE, READ_ONLY or READ_WRITE. RW_DELETE is stored as READ_WRITE."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after setting a mount policy.",
    ),
    model=SetPayloadDTO,
    name="SetVFolderMountPolicyPayload",
)
class SetVFolderMountPolicyPayloadGQL(PydanticOutputMixin[SetPayloadDTO]):
    policy: VFolderMountPolicyGQL = gql_field(description="The mount level now set.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Input for taking back the mount level one user was given on a virtual folder.",
    ),
    name="UnsetVFolderMountPolicyInput",
)
class UnsetVFolderMountPolicyInputGQL(PydanticInputMixin[UnsetInputDTO]):
    user_id: UUID = gql_field(description="User whose mount level is taken back.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after unsetting a mount policy.",
    ),
    model=UnsetPayloadDTO,
    name="UnsetVFolderMountPolicyPayload",
)
class UnsetVFolderMountPolicyPayloadGQL(PydanticOutputMixin[UnsetPayloadDTO]):
    vfolder_id: UUID = gql_field(description="ID of the virtual folder.")
    user_id: UUID = gql_field(description="User whose mount level was taken back.")
    removed: bool = gql_field(description="Whether a row was removed.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="The mount levels set on a virtual folder, one row per user.",
    ),
    model=ListPayloadDTO,
    name="VFolderMountPoliciesPayload",
)
class VFolderMountPoliciesPayloadGQL(PydanticOutputMixin[ListPayloadDTO]):
    items: list[VFolderMountPolicyGQL] = gql_field(description="One row per user.")
