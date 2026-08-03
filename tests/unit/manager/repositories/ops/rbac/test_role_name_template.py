"""Tests for the Jinja-based role name templating.

Verifies the rendering contract used when instantiating roles from role
presets: scope variables are substituted, and bad templates (syntax errors,
undefined variables, unusable results, sandbox escapes) are rejected with
``InvalidRoleNameTemplate``.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.errors.role_preset import InvalidRoleNameTemplate
from ai.backend.manager.repositories.ops.rbac.provider import (
    MAX_ROLE_NAME_LENGTH,
    RBACWriteOps,
)


@pytest.fixture
def write_ops() -> RBACWriteOps:
    # Rendering and validation never touch the session, so a mock session suffices.
    return RBACWriteOps(MagicMock())


@pytest.fixture
def scope_value() -> ScopeTemplateValue:
    return ScopeTemplateValue(
        id=uuid.UUID("8f9a2f6c-0000-0000-0000-000000000000"),
        name="myproject",
        type="project",
    )


class TestRenderRoleName:
    def test_renders_scope_variables(
        self, write_ops: RBACWriteOps, scope_value: ScopeTemplateValue
    ) -> None:
        assert (
            write_ops._render_role_name("{{ scope.name }}-member", scope_value)
            == "myproject-member"
        )
        assert write_ops._render_role_name("{{ scope.type }}:{{ scope.name }}", scope_value) == (
            "project:myproject"
        )
        assert write_ops._render_role_name("role-{{ scope.id }}", scope_value) == (
            "role-8f9a2f6c-0000-0000-0000-000000000000"
        )

    def test_surrounding_whitespace_is_stripped(
        self, write_ops: RBACWriteOps, scope_value: ScopeTemplateValue
    ) -> None:
        assert write_ops._render_role_name("  {{ scope.name }}  ", scope_value) == "myproject"

    def test_undefined_variable_raises(
        self, write_ops: RBACWriteOps, scope_value: ScopeTemplateValue
    ) -> None:
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops._render_role_name("{{ scope.unknown }}-member", scope_value)
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops._render_role_name("{{ unknown }}-member", scope_value)

    def test_syntax_error_raises(
        self, write_ops: RBACWriteOps, scope_value: ScopeTemplateValue
    ) -> None:
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops._render_role_name("{{ scope.name -member", scope_value)

    def test_blank_result_raises(
        self, write_ops: RBACWriteOps, scope_value: ScopeTemplateValue
    ) -> None:
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops._render_role_name("{{ ' ' }}", scope_value)

    def test_too_long_result_raises(
        self, write_ops: RBACWriteOps, scope_value: ScopeTemplateValue
    ) -> None:
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops._render_role_name("x" * (MAX_ROLE_NAME_LENGTH + 1), scope_value)

    def test_sandbox_blocks_internal_attribute_access(
        self, write_ops: RBACWriteOps, scope_value: ScopeTemplateValue
    ) -> None:
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops._render_role_name("{{ scope.__class__ }}", scope_value)


class TestValidateRoleNameTemplate:
    def test_accepts_valid_template(self, write_ops: RBACWriteOps) -> None:
        write_ops.validate_role_name_template("{{ scope.name }}-member")

    def test_rejects_undefined_variable(self, write_ops: RBACWriteOps) -> None:
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops.validate_role_name_template("{{ scope.unknown }}-member")

    def test_rejects_syntax_error(self, write_ops: RBACWriteOps) -> None:
        with pytest.raises(InvalidRoleNameTemplate):
            write_ops.validate_role_name_template("{% if %}")
