"""Validators for prometheus_query_preset templates."""

from __future__ import annotations

import re
from collections.abc import Iterator

from jinja2 import StrictUndefined, TemplateError, TemplateSyntaxError, nodes
from jinja2.sandbox import ImmutableSandboxedEnvironment

from ai.backend.common.exception import InvalidMetricPresetTemplate

__all__ = (
    "PLACEHOLDER_NAMES",
    "PROMQL_TEMPLATE_ENV",
    "validate_query_template",
)

PLACEHOLDER_NAMES = frozenset({"labels", "window", "group_by"})

# Sandboxed: templates are user input from the admin API.
PROMQL_TEMPLATE_ENV = ImmutableSandboxedEnvironment(undefined=StrictUndefined)

# Literal text and `{{ placeholder }}` substitution only.
_ALLOWED_NODE_TYPES = (nodes.Template, nodes.Output, nodes.TemplateData, nodes.Name)

_UNSUPPORTED_TEMPLATE_VAR_RE = re.compile(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*")
# Bare `{placeholder}` or any `{{{`: the pre-Jinja str.format syntax.
_LEGACY_TEMPLATE_RE = re.compile(r"(?<!\{)\{(?:labels|window|group_by)\}(?!\})|\{\{\{")


def _walk(node: nodes.Node) -> Iterator[nodes.Node]:
    yield node
    for child in node.iter_child_nodes():
        yield from _walk(child)


def validate_query_template(template: str) -> None:
    """Validate a Jinja PromQL template; raises ``InvalidMetricPresetTemplate``."""
    if not template.strip():
        raise InvalidMetricPresetTemplate("Template must not be empty.")
    unsupported_vars = _UNSUPPORTED_TEMPLATE_VAR_RE.findall(template)
    if unsupported_vars:
        placeholders = ", ".join(f"{{{{ {name} }}}}" for name in sorted(PLACEHOLDER_NAMES))
        raise InvalidMetricPresetTemplate(
            f"Unsupported template variables: {unsupported_vars}. "
            f"Use placeholders {placeholders} or literal PromQL values."
        )
    if _LEGACY_TEMPLATE_RE.search(template):
        raise InvalidMetricPresetTemplate(
            "Legacy str.format template syntax is no longer supported; "
            f"use {{{{ labels }}}}, {{{{ window }}}}, {{{{ group_by }}}}: {template!r}"
        )
    try:
        ast = PROMQL_TEMPLATE_ENV.parse(template)
    except TemplateSyntaxError as e:
        raise InvalidMetricPresetTemplate(f"Invalid template syntax ({e}): {template!r}") from e
    for node in _walk(ast):
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            raise InvalidMetricPresetTemplate(
                f"Only {{{{ placeholder }}}} substitution is allowed; "
                f"found {type(node).__name__}: {template!r}"
            )
    try:
        # Smoke-render with empty values; StrictUndefined rejects unknown variables.
        PROMQL_TEMPLATE_ENV.from_string(template).render(labels="", window="", group_by="")
    except TemplateError as e:
        raise InvalidMetricPresetTemplate(
            f"Failed to render PromQL template ({type(e).__name__}: {e}): {template!r}"
        ) from e
