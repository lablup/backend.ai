"""Role preset GQL mutation payload types."""

from __future__ import annotations

from uuid import UUID

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
    UpdateRolePresetPayload as UpdateRolePresetPayloadDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
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
