"""Action-layer validation of a role preset's ``role_name_template``."""

from __future__ import annotations

import dataclasses
import uuid
from typing import ClassVar, override

import jinja2
import jinja2.sandbox

from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.validator.base import GlobalActionValidator
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.errors.role_preset import InvalidRoleNameTemplate
from ai.backend.manager.services.role_preset.actions.base import RoleNameTemplateCarrier

__all__ = ("RoleNameTemplateValidator",)


class RoleNameTemplateValidator(GlobalActionValidator):
    """Renders the template against representative values and refuses a broken one.

    The framework hands validators the shape base, so the carrier interface is
    narrowed here — this reads what the action holds, it does not select a write
    path, which is where runtime type checks are ruled out.
    """

    # Rendered role names are stored in ``roles.name`` (sa.String(64)).
    _MAX_ROLE_NAME_LENGTH: ClassVar[int] = 64

    _template_env: jinja2.sandbox.ImmutableSandboxedEnvironment

    def __init__(self) -> None:
        self._template_env = jinja2.sandbox.ImmutableSandboxedEnvironment(
            undefined=jinja2.StrictUndefined,
        )

    @override
    async def validate(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        if not isinstance(action, RoleNameTemplateCarrier):
            return
        template = action.role_name_template()
        if template is None:
            return
        dummy = ScopeTemplateValue(id=uuid.UUID(int=0), name="name", type="user")
        try:
            rendered = self._template_env.from_string(template).render(
                scope=dataclasses.asdict(dummy),
            )
        except jinja2.TemplateError as e:
            raise InvalidRoleNameTemplate(f"Failed to render role name template: {e}") from e
        rendered = rendered.strip()
        if not rendered:
            raise InvalidRoleNameTemplate("Role name template rendered to an empty string.")
        if len(rendered) > self._MAX_ROLE_NAME_LENGTH:
            raise InvalidRoleNameTemplate(
                f"Rendered role name exceeds {self._MAX_ROLE_NAME_LENGTH} characters: {rendered!r}"
            )
