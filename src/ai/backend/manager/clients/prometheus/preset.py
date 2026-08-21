import re
from collections.abc import Callable, Iterator, Mapping, Sequence, Set
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from typing import Final, Self

from jinja2 import (
    StrictUndefined,
    Template,
    TemplateError,
    TemplateSyntaxError,
    UndefinedError,
    nodes,
)
from jinja2.sandbox import ImmutableSandboxedEnvironment

from ai.backend.common.exception import InvalidMetricPresetTemplate

PLACEHOLDER_NAMES = frozenset({"labels", "window", "group_by"})

# PromQL uses braces for label selectors, so the default `{{ }}` would collide
# with the query language itself. `${{ }}` (GitHub Actions syntax) does not: a
# lone `${` can occur in literal PromQL (a `$` regex anchor before a `{n}`
# quantifier), while `${{` cannot.
_VARIABLE_START, _VARIABLE_END = "${{", "}}"

# Literal text and `${{ placeholder }}` substitution only; statements and comments
# reach the parser but are rejected here.
_ALLOWED_NODE_TYPES = (nodes.Template, nodes.Output, nodes.TemplateData, nodes.Name)

# Bare `{placeholder}` or any `{{{`: the pre-${{ }} str.format syntax.
_LEGACY_TEMPLATE_RE = re.compile(r"(?<![{$])\{(?:labels|window|group_by)\}(?!\})|\{\{\{")
_PLACEHOLDER_HELP: Final[str] = ", ".join(
    f"{_VARIABLE_START}{name}{_VARIABLE_END}" for name in sorted(PLACEHOLDER_NAMES)
)


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


def _walk(node: nodes.Node) -> Iterator[nodes.Node]:
    yield node
    for child in node.iter_child_nodes():
        yield from _walk(child)


def _escape_label_value(value: str) -> str:
    # PromQL string literals: escape backslash, double quote, newline, carriage return
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


@dataclass(frozen=True)
class MetricPreset:
    """PromQL query preset with a template
    (placeholders: ``${{labels}}``, ``${{window}}``, ``${{group_by}}``)."""

    template: str

    # Injected into ${{labels}}
    labels: Mapping[str, LabelMatcher] = field(default_factory=dict)

    # Injected into ${{group_by}}
    group_by: Set[str] = field(default_factory=frozenset)

    # Injected into ${{window}}
    window: str = ""


class PromQLTemplateRenderer:
    """Validates and renders PromQL Jinja templates in a sandboxed environment."""

    _env: ImmutableSandboxedEnvironment
    _compile: Callable[[str], Template]

    def __init__(self) -> None:
        # Sandboxed: templates are user input from the admin API.
        self._env = ImmutableSandboxedEnvironment(
            variable_start_string=_VARIABLE_START,
            variable_end_string=_VARIABLE_END,
            undefined=StrictUndefined,
        )
        self._compile = lru_cache(maxsize=256)(self._env.from_string)

    def validate(self, template: str) -> None:
        """Validate a PromQL Jinja template; raises ``InvalidMetricPresetTemplate``."""
        if not template.strip():
            raise InvalidMetricPresetTemplate("Template must not be empty.")
        if _LEGACY_TEMPLATE_RE.search(template):
            raise InvalidMetricPresetTemplate(
                "Legacy str.format template syntax is no longer supported; "
                f"use {_PLACEHOLDER_HELP}: {template!r}"
            )
        try:
            ast = self._env.parse(template)
        except TemplateSyntaxError as e:
            raise InvalidMetricPresetTemplate(f"Invalid template syntax ({e}): {template!r}") from e
        for node in _walk(ast):
            if not isinstance(node, _ALLOWED_NODE_TYPES):
                raise InvalidMetricPresetTemplate(
                    f"Only {_VARIABLE_START} placeholder {_VARIABLE_END} substitution is allowed; "
                    f"found {type(node).__name__}: {template!r}"
                )
        try:
            # Smoke-render with empty values; StrictUndefined rejects unknown variables.
            self._compile(template).render(labels="", window="", group_by="")
        except UndefinedError as e:
            raise InvalidMetricPresetTemplate(
                f"Unsupported template variable ({e}). "
                f"Use placeholders {_PLACEHOLDER_HELP} or literal PromQL values."
            ) from e
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
