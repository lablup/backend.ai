"""Role preset domain exceptions."""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.role_permission_preset import RolePermissionPresetFieldType
from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode


class InvalidRoleNameTemplate(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-role-name-template"
    error_title = "Invalid role name template."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            RolePresetEntityType(), ActionOperationType.CREATE, ErrorDetail.INVALID_PARAMETERS
        )


class SystemRoleNotEditable(EntityError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/system-role-not-editable"
    error_title = "A SYSTEM role cannot be purged; edit the role preset instead."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(RoleEntityType(), ActionOperationType.PURGE, ErrorDetail.FORBIDDEN)


class RolePermissionPresetConflict(FieldError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-role-permission-preset"
    error_title = "Duplicate role permission preset entry."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            RolePermissionPresetFieldType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )
