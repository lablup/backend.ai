"""Jinja-based name templating for roles instantiated from role presets.

A role preset may carry a ``name_template`` (e.g. ``{{scope.type}}-{{scope.name}}-member``).
When a role is instantiated from the preset, the template is rendered with the
target scope's attributes to produce a per-scope role name instead of the
preset's fixed name. Scope resolution and rendering at instantiation time live
in :mod:`ai.backend.manager.repositories.ops.rbac.provider`; this module owns
the rendering and the create/update-time validation.
"""

from __future__ import annotations

import dataclasses
import uuid

import jinja2
import jinja2.sandbox

from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.errors.role_preset import InvalidRoleNameTemplate

# Rendered names are stored in ``roles.name`` (sa.String(64)).
MAX_ROLE_NAME_LENGTH = 64

_template_env = jinja2.sandbox.ImmutableSandboxedEnvironment(
    undefined=jinja2.StrictUndefined,
)


def render_role_name(template: str, scope: ScopeTemplateValue) -> str:
    """Render a role name from the template, raising :class:`InvalidRoleNameTemplate`
    on syntax errors, undefined variables, or an unusable result."""
    try:
        rendered = _template_env.from_string(template).render(
            scope=dataclasses.asdict(scope),
        )
    except jinja2.TemplateError as e:
        raise InvalidRoleNameTemplate(f"Failed to render role name template: {e}") from e
    rendered = rendered.strip()
    if not rendered:
        raise InvalidRoleNameTemplate("Role name template rendered to an empty string.")
    if len(rendered) > MAX_ROLE_NAME_LENGTH:
        raise InvalidRoleNameTemplate(
            f"Rendered role name exceeds {MAX_ROLE_NAME_LENGTH} characters: {rendered!r}"
        )
    return rendered


def validate_role_name_template(template: str) -> None:
    """Validate a template by rendering it against representative dummy values,
    so syntax errors and undefined variables are rejected before the preset
    is stored."""
    dummy = ScopeTemplateValue(
        id=uuid.UUID(int=0),
        name="example-scope",
        type="user",
    )
    render_role_name(template, dummy)
