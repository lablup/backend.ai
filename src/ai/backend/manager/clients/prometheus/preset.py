import re
from collections.abc import Mapping, Set
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from ai.backend.common.exception import InvalidMetricPresetTemplate

_PLACEHOLDER_NAMES = frozenset({"labels", "window", "group_by"})
_BRACE_BLOCK_RE = re.compile(r"\{([^{}]*)\}")


def _escape_non_placeholders(template: str) -> str:
    # Normalize each `{X}` so str.format produces a single PromQL `{value}`
    # regardless of how many braces the user wrote.
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        start, end = match.span()
        text = match.string
        already_wrapped = (
            start > 0 and text[start - 1] == "{" and end < len(text) and text[end] == "}"
        )
        if name not in _PLACEHOLDER_NAMES:
            return match.group(0) if already_wrapped else "{{" + name + "}}"
        if name != "labels":
            return match.group(0)
        return match.group(0) if already_wrapped else "{{" + match.group(0) + "}}"

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
