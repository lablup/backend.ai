"""Role preset GQL mutation payload types."""

from __future__ import annotations

from uuid import UUID

import strawberry

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkDeleteRolePresetsPayload as BulkDeleteRolePresetsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkPurgeRolePresetsPayload as BulkPurgeRolePresetsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkRestoreRolePresetsPayload as BulkRestoreRolePresetsPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkRolePresetFailureInfo as BulkRolePresetFailureInfoDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    CreateRolePresetPayload as CreateRolePresetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    DeleteRolePresetPayload as DeleteRolePresetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    PurgeRolePresetPayload as PurgeRolePresetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    RestoreRolePresetPayload as RestoreRolePresetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.common.dto.manager.v2.role_preset.response import (
    UpdateRolePresetPayload as UpdateRolePresetPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import PartialBulkFailureGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

from .node import RolePresetGQL


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after creating a role preset.",
    ),
    model=CreateRolePresetPayloadDTO,
    name="CreateRolePresetPayload",
)
class CreateRolePresetPayloadGQL(PydanticOutputMixin[CreateRolePresetPayloadDTO]):
    role_preset: RolePresetGQL = gql_field(description="Created role preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after updating a role preset.",
    ),
    model=UpdateRolePresetPayloadDTO,
    name="UpdateRolePresetPayload",
)
class UpdateRolePresetPayloadGQL(PydanticOutputMixin[UpdateRolePresetPayloadDTO]):
    role_preset: RolePresetGQL = gql_field(description="Updated role preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Failure detail for a single role preset ID in a bulk operation.",
    ),
    model=BulkRolePresetFailureInfoDTO,
    name="BulkRolePresetFailureInfo",
)
class BulkRolePresetFailureInfoGQL(PydanticOutputMixin[BulkRolePresetFailureInfoDTO]):
    role_preset_id: UUID = gql_field(description="Role preset ID that the operation failed on.")
    message: str = gql_field(description="Error message describing the failure.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after bulk-soft-deleting role presets.",
    ),
    model=BulkDeleteRolePresetsPayloadDTO,
    name="BulkDeleteRolePresetsPayload",
)
class BulkDeleteRolePresetsPayloadGQL(PydanticOutputMixin[BulkDeleteRolePresetsPayloadDTO]):
    items: list[RolePresetGQL] = gql_field(description="Role presets that were soft-deleted.")
    failed: list[BulkRolePresetFailureInfoGQL] = gql_field(
        description="Role preset IDs that failed to soft-delete."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after bulk-restoring soft-deleted role presets.",
    ),
    model=BulkRestoreRolePresetsPayloadDTO,
    name="BulkRestoreRolePresetsPayload",
)
class BulkRestoreRolePresetsPayloadGQL(PydanticOutputMixin[BulkRestoreRolePresetsPayloadDTO]):
    items: list[RolePresetGQL] = gql_field(description="Role presets that were restored.")
    failed: list[BulkRolePresetFailureInfoGQL] = gql_field(
        description="Role preset IDs that failed to restore."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Payload returned after bulk-hard-deleting role presets.",
    ),
    model=BulkPurgeRolePresetsPayloadDTO,
    name="BulkPurgeRolePresetsPayload",
)
class BulkPurgeRolePresetsPayloadGQL(PydanticOutputMixin[BulkPurgeRolePresetsPayloadDTO]):
    items: list[RolePresetGQL] = gql_field(description="Role presets that were purged.")
    failed: list[BulkRolePresetFailureInfoGQL] = gql_field(
        description="Role preset IDs that failed to purge."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after soft-deleting a role preset.",
    ),
    model=DeleteRolePresetPayloadDTO,
    name="DeleteRolePresetPayload",
)
class DeleteRolePresetPayloadGQL(PydanticOutputMixin[DeleteRolePresetPayloadDTO]):
    role_preset: RolePresetGQL = gql_field(description="Soft-deleted role preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after restoring a role preset.",
    ),
    model=RestoreRolePresetPayloadDTO,
    name="RestoreRolePresetPayload",
)
class RestoreRolePresetPayloadGQL(PydanticOutputMixin[RestoreRolePresetPayloadDTO]):
    role_preset: RolePresetGQL = gql_field(description="Restored role preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload returned after purging a role preset.",
    ),
    model=PurgeRolePresetPayloadDTO,
    name="PurgeRolePresetPayload",
)
class PurgeRolePresetPayloadGQL(PydanticOutputMixin[PurgeRolePresetPayloadDTO]):
    role_preset: RolePresetGQL = gql_field(
        description="Purged role preset, as it stood.",
        deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgedId` or `entityId`.",
    )
    purged_id: strawberry.ID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Global ID of the purged role preset.",
        ),
    )
    entity_id: UUID = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION, description="UUID of the purged role preset."
        ),
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Result of a partial bulk role preset operation: the role presets processed and the "
            "ones that failed."
        ),
    ),
    model=PartialBulkPayload[RolePresetNode],
    name="PartialBulkRolePresetsPayload",
)
class PartialBulkRolePresetsPayloadGQL(PydanticOutputMixin[PartialBulkPayload[RolePresetNode]]):
    successes: list[RolePresetGQL] = gql_field(
        description="The role presets processed, as they now stand."
    )
    failed: list[PartialBulkFailureGQL] = gql_field(
        description="The role presets not processed, each with the reason."
    )
