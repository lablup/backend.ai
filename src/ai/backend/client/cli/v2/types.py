"""Reusable Click parameter types for v2 CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import click


@dataclass(frozen=True)
class ScopeArg:
    """Parsed ``--scope <type>:<id>`` CLI value.

    Both fields are kept as raw strings; domain-specific interpretation (e.g.
    mapping ``type`` to an enum, parsing ``id`` as UUID) is the caller's
    responsibility.
    """

    type: str
    id: str


class ScopeArgType(click.ParamType):
    """Click parameter type for ``<type>:<id>`` scope arguments.

    Validates syntax only — splits on the first ``:`` and checks that both
    sides are non-empty. Returns a :class:`ScopeArg` with raw string fields.
    """

    name = "scope"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> ScopeArg:
        if isinstance(value, ScopeArg):
            return value
        if not isinstance(value, str) or ":" not in value:
            self.fail(f"must be in '<type>:<id>' form (got: {value!r})", param, ctx)
        type_part, id_part = value.split(":", 1)
        type_part = type_part.strip()
        id_part = id_part.strip()
        if not type_part or not id_part:
            self.fail(f"requires both type and id (got: {value!r})", param, ctx)
        return ScopeArg(type=type_part, id=id_part)
