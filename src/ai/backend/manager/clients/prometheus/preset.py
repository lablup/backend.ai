import re
from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, Self

from ai.backend.common.exception import InvalidMetricPresetTemplate

PLACEHOLDER_NAMES = frozenset({"labels", "window", "group_by"})

# `${labels}`, `${window}`, `${group_by}`; every other character is literal PromQL.
_PLACEHOLDER_RE = re.compile(r"\$\{(" + "|".join(sorted(PLACEHOLDER_NAMES)) + r")\}")
# Any `$`-sigil variable, so unknown ones can be reported instead of silently kept as literals.
_ANY_VAR_RE = re.compile(r"\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*")
# Bare `{placeholder}` or any `{{{`: the pre-${} str.format syntax.
_LEGACY_TEMPLATE_RE = re.compile(r"(?<![{$])\{(?:labels|window|group_by)\}(?!\})|\{\{\{")
_PLACEHOLDER_HELP: Final[str] = ", ".join(f"${{{name}}}" for name in sorted(PLACEHOLDER_NAMES))


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


def regex_union(values: Sequence[str]) -> str:
    return "|".join(re.escape(value).replace(r"\-", "-") for value in values)


def _escape_label_value(value: str) -> str:
    # PromQL string literals: escape backslash, double quote, newline, carriage return
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


@dataclass(frozen=True)
class MetricPreset:
    """PromQL query preset with a template
    (placeholders: ``${labels}``, ``${window}``, ``${group_by}``)."""

    template: str

    # Injected into ${labels}
    labels: Mapping[str, LabelMatcher] = field(default_factory=dict)

    # Injected into ${group_by}
    group_by: Set[str] = field(default_factory=frozenset)

    # Injected into ${window}
    window: str = ""


class PromQLTemplateRenderer:
    """Validates and renders PromQL templates built from a fixed placeholder set."""

    def validate(self, template: str) -> None:
        """Validate a PromQL template; raises ``InvalidMetricPresetTemplate``."""
        if not template.strip():
            raise InvalidMetricPresetTemplate("Template must not be empty.")
        unsupported_vars = [
            match.group()
            for match in _ANY_VAR_RE.finditer(template)
            if not _PLACEHOLDER_RE.fullmatch(match.group())
        ]
        if unsupported_vars:
            raise InvalidMetricPresetTemplate(
                f"Unsupported template variables: {unsupported_vars}. "
                f"Use placeholders {_PLACEHOLDER_HELP} or literal PromQL values."
            )
        if _LEGACY_TEMPLATE_RE.search(template):
            raise InvalidMetricPresetTemplate(
                "Legacy str.format template syntax is no longer supported; "
                f"use {_PLACEHOLDER_HELP}: {template!r}"
            )

    def render(self, preset: MetricPreset) -> str:
        """Render the PromQL query with all preset values injected."""
        label_str = ",".join(
            f'{key}{value.operator}"{_escape_label_value(value.value)}"'
            for key, value in preset.labels.items()
        )
        values = {
            "labels": label_str,
            "window": preset.window,
            "group_by": ",".join(sorted(preset.group_by)),
        }
        return _PLACEHOLDER_RE.sub(lambda match: values[match.group(1)], preset.template)
