from collections.abc import Mapping, Set
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LabelMatcher:
    """PromQL label matcher with an explicit operator."""

    value: str
    operator: str = "="

    @classmethod
    def exact(cls, value: str) -> "LabelMatcher":
        return cls(value=value, operator="=")

    @classmethod
    def regex(cls, value: str) -> "LabelMatcher":
        return cls(value=value, operator="=~")


def _escape_label_value(value: str) -> str:
    # PromQL string literals: escape backslash, double quote, newline, carriage return
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


@dataclass(frozen=True)
class MetricPreset:
    """PromQL query preset with template and injectable values."""

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
        return self.template.format(
            labels=label_str,
            window=self.window,
            group_by=",".join(sorted(self.group_by)),  # sorted for consistency
        )
