from __future__ import annotations

import dataclasses
import uuid

import jinja2
import jinja2.sandbox

from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityWithFieldsOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.errors.role_preset import InvalidRoleNameTemplate
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.role_preset.actions.create import CreateRolePresetAction
from ai.backend.manager.services.role_preset.actions.update import UpdateRolePresetAction

__all__ = ("RolePresetService",)


class RolePresetService:
    """The two writes that settle a preset's ``role_name_template``.

    Every other operation of this domain runs straight against ops; these two branch,
    so they are the whole of this service.
    """

    _repository: OpsRepository[RolePresetData]
    _template_env: jinja2.sandbox.ImmutableSandboxedEnvironment

    def __init__(self, repository: OpsRepository[RolePresetData]) -> None:
        self._repository = repository
        self._template_env = jinja2.sandbox.ImmutableSandboxedEnvironment(
            undefined=jinja2.StrictUndefined,
        )

    async def create(
        self, action: CreateRolePresetAction
    ) -> CreatedEntityWithFieldsOpsResult[RolePresetData, RolePermissionPresetData]:
        self._reject_unrenderable(action.creator.role_name_template)
        result = await self._repository.create_global_entity_with_fields(
            action.to_creator(), action.to_field_creators()
        )
        return CreatedEntityWithFieldsOpsResult(data=result.data, fields=result.fields)

    async def update(self, action: UpdateRolePresetAction) -> EntityOpsResult[RolePresetData]:
        template = action.updater.role_name_template
        if template.is_update():
            self._reject_unrenderable(template.value())
        return EntityOpsResult(data=await self._repository.update(action.to_updater()))

    def _reject_unrenderable(self, template: str | None) -> None:
        """Render the template against representative values and refuse a broken one.

        The render at use time swallows its own failure and falls back to a generated
        name, so this is the only point a caller learns the template is broken.
        """
        if template is None:
            return
        dummy = ScopeTemplateValue(id=uuid.UUID(int=0), name="name", type="user")
        try:
            rendered = self._template_env.from_string(template).render(
                scope=dataclasses.asdict(dummy),
            )
        except jinja2.TemplateError as e:
            raise InvalidRoleNameTemplate(f"Failed to render role name template: {e}") from e
        if not rendered.strip():
            raise InvalidRoleNameTemplate("Role name template rendered to an empty string.")
