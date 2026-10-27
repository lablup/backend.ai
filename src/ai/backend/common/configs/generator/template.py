"""Render a generated sample template into a configuration file."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping

import jinja2

__all__ = ("render_config_template",)


def render_config_template(template: str, args: Mapping[str, str]) -> str:
    """Fill the template arguments and check that the result parses as TOML.

    A missing argument raises ``jinja2.UndefinedError`` and a result that is not TOML
    raises ``tomllib.TOMLDecodeError``, so nothing is written from a half-filled template.
    """
    env = jinja2.Environment(undefined=jinja2.StrictUndefined, keep_trailing_newline=True)
    rendered = env.from_string(template).render(args)
    tomllib.loads(rendered)
    return rendered
