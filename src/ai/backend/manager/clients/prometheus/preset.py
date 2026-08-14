import re
from collections.abc import Callable, Iterator, Mapping, Sequence, Set
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from typing import Self

from jinja2 import StrictUndefined, Template, TemplateError, TemplateSyntaxError, nodes
from jinja2.sandbox import ImmutableSandboxedEnvironment

from ai.backend.common.exception import InvalidMetricPresetTemplate

PLACEHOLDER_NAMES = frozenset({"labels", "window", "group_by"})

# Literal text and `{{ placeholder }}` substitution only.
_ALLOWED_NODE_TYPES = (nodes.Template, nodes.Output, nodes.TemplateData, nodes.Name)

_UNSUPPORTED_TEMPLATE_VAR_RE = re.compile(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*")
# Bare `{placeholder}` or any `{{{`: the pre-Jinja str.format syntax.
_LEGACY_TEMPLATE_RE = re.compile(r"(?<!\{)\{(?:labels|window|group_by)\}(?!\})|\{\{\{")


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


def _walk(node: nodes.Node) -> Iterator[nodes.Node]:
    yield node
    for child in node.iter_child_nodes():
        yield from _walk(child)


@dataclass(frozen=True)
class MetricPreset:
    """PromQL query preset with a Jinja template
    (placeholders: ``{{ labels }}``, ``{{ window }}``, ``{{ group_by }}``)."""

    template: str

    # Injected into {{ labels }}
    labels: Mapping[str, LabelMatcher] = field(default_factory=dict)

    # Injected into {{ group_by }}
    group_by: Set[str] = field(default_factory=frozenset)

    # Injected into {{ window }}
    window: str = ""


class PromQLTemplateRenderer:
    """Validates and renders PromQL Jinja templates in a sandboxed environment."""

    _env: ImmutableSandboxedEnvironment
    _compile: Callable[[str], Template]

    def __init__(self) -> None:
        # Sandboxed: templates are user input from the admin API.
        self._env = ImmutableSandboxedEnvironment(undefined=StrictUndefined)
        self._compile = lru_cache(maxsize=256)(self._env.from_string)

    def validate(self, template: str) -> None:
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
            ast = self._env.parse(template)
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
            self._compile(template).render(labels="", window="", group_by="")
        except TemplateError as e:
            raise InvalidMetricPresetTemplate(
                f"Failed to render PromQL template ({type(e).__name__}: {e}): {template!r}"
            ) from e

    def render(self, preset: MetricPreset) -> str:
        """Render the PromQL query with all preset values injected."""
        label_str = ",".join(
            f'{key}{value.operator}"{_escape_label_value(value.value)}"'
            for key, value in preset.labels.items()
        )
        try:
            return self._compile(preset.template).render(
                labels=label_str,
                window=preset.window,
                group_by=",".join(sorted(preset.group_by)),
            )
        except TemplateError as e:
            raise InvalidMetricPresetTemplate(
                f"Failed to render PromQL template ({type(e).__name__}: {e}): {preset.template!r}"
            ) from e
