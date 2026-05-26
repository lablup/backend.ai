"""Request DTO validators for prometheus_query_preset templates."""

from __future__ import annotations

import re

from ai.backend.common.exception import InvalidMetricPresetTemplate

__all__ = (
    "PLACEHOLDER_NAMES",
    "escape_non_placeholders",
    "validate_query_template",
)

PLACEHOLDER_NAMES = frozenset({"labels", "window", "group_by"})

_BRACE_BLOCK_RE = re.compile(r"\{([^{}]*)\}")
_UNSUPPORTED_TEMPLATE_VAR_RE = re.compile(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*")


def escape_non_placeholders(template: str) -> str:
    """Normalize each ``{X}`` so ``str.format`` produces a single PromQL ``{value}``
    regardless of how many braces the user wrote.
    """

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        start, end = match.span()
        text = match.string
        already_wrapped = (
            start > 0 and text[start - 1] == "{" and end < len(text) and text[end] == "}"
        )
        if name not in PLACEHOLDER_NAMES:
            return match.group(0) if already_wrapped else "{{" + name + "}}"
        if name != "labels":
            return match.group(0)
        return match.group(0) if already_wrapped else "{{" + match.group(0) + "}}"

    return _BRACE_BLOCK_RE.sub(repl, template)


def validate_query_template(template: str) -> str:
    """Reject empty templates, foreign variables, or malformed braces."""
    if not template.strip():
        raise InvalidMetricPresetTemplate("Template must not be empty.")
    unsupported_vars = _UNSUPPORTED_TEMPLATE_VAR_RE.findall(template)
    if unsupported_vars:
        placeholders = ", ".join(f"{{{name}}}" for name in sorted(PLACEHOLDER_NAMES))
        raise InvalidMetricPresetTemplate(
            f"Unsupported template variables: {unsupported_vars}. "
            f"Use placeholders {placeholders} or literal PromQL values."
        )
    try:
        escape_non_placeholders(template).format(labels="", window="", group_by="")
    except (ValueError, KeyError, IndexError) as e:
        raise InvalidMetricPresetTemplate(
            f"Failed to render PromQL template ({type(e).__name__}: {e}): {template!r}"
        ) from e
    return template
