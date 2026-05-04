import re
from collections.abc import Mapping, Set
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from ai.backend.common.exception import InvalidMetricPresetTemplate

_PLACEHOLDER_NAMES = frozenset({"labels", "window", "group_by"})
_BRACE_BLOCK_RE = re.compile(r"\{([^{}]*)\}")
# Matches `$ident` / `${ident}` — foreign template syntax (Grafana, shell, etc.)
# that Backend.AI does not substitute and Prometheus would reject.
_UNSUPPORTED_TEMPLATE_VAR_RE = re.compile(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*")


def validate_query_template(template: str) -> None:
    """Reject templates with foreign variables or malformed braces."""
    unsupported_vars = _UNSUPPORTED_TEMPLATE_VAR_RE.findall(template)
    if unsupported_vars:
        raise InvalidMetricPresetTemplate(
            f"Unsupported template variables: {unsupported_vars}. "
            "Use placeholders {labels}, {window}, {group_by} or literal PromQL values."
        )
    # Check for malformed braces by attempting to render with dummy values.
    MetricPreset(template=template).render()


def _escape_non_placeholders(template: str) -> str:
    # PromQL label matchers `{key=...}` collide with str.format placeholders;
    # escape any non-placeholder `{...}` block so .format treats it as literal.
    def repl(match: re.Match[str]) -> str:
        if match.group(1) in _PLACEHOLDER_NAMES:
            return match.group(0)
        return "{{" + match.group(1) + "}}"

    return _BRACE_BLOCK_RE.sub(repl, template)


class LabelOperator(StrEnum):
    EQUAL = "="
    NOT_EQUAL = "!="
    REGEX = "=~"
    NOT_REGEX = "!~"


@dataclass(frozen=True)
class LabelMatcher:
    """PromQL label matcher with an explicit operator."""

    value: str
    operator: LabelOperator = LabelOperator.EQUAL

    @classmethod
    def exact(cls, value: str) -> Self:
        return cls(value=value, operator=LabelOperator.EQUAL)

    @classmethod
    def regex(cls, value: str) -> Self:
        return cls(value=value, operator=LabelOperator.REGEX)


def _escape_label_value(value: str) -> str:
    # PromQL string literals: escape backslash, double quote, newline, carriage return
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


@dataclass(frozen=True)
class MetricPreset:
    """PromQL query preset with template (placeholders: {labels}, {window}, {group_by})."""

    # PromQL template (placeholders: {labels}, {window}, {group_by})
    template: str

    # Query labels (injected into {labels} placeholder)
    labels: Mapping[str, LabelMatcher] = field(default_factory=dict)

    # Group by labels (injected into {group_by} placeholder)
    group_by: Set[str] = field(default_factory=frozenset)

    # Window (injected into {window} placeholder)
    window: str = ""

    def render(self) -> str:
        """Render the PromQL query with all values injected."""
        label_str = ",".join(
            f'{key}{value.operator}"{_escape_label_value(value.value)}"'
            for key, value in self.labels.items()
        )
        try:
            return _escape_non_placeholders(self.template).format(
                labels=label_str,
                window=self.window,
                group_by=",".join(sorted(self.group_by)),
            )
        except (ValueError, KeyError, IndexError) as e:
            raise InvalidMetricPresetTemplate(
                f"Failed to render PromQL template ({type(e).__name__}: {e}): {self.template!r}"
            ) from e
