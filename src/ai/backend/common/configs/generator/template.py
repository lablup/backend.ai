"""Render a generated sample template into a configuration file."""

from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Mapping

import jinja2

__all__ = ("render_config_template",)

_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")


def _toml_key(value: str) -> str:
    """Quote a key that is not a TOML bare key, so `local.ssd` stays one key instead of two tables."""
    return value if _BARE_KEY.fullmatch(value) else json.dumps(value, ensure_ascii=False)


def render_config_template(template: str, args: Mapping[str, str]) -> str:
    """Fill the template arguments and check that the result parses as TOML.

    A missing argument raises ``jinja2.UndefinedError`` and a result that is not TOML
    raises ``tomllib.TOMLDecodeError``, so nothing is written from a half-filled template.
    """
    env = jinja2.Environment(undefined=jinja2.StrictUndefined, keep_trailing_newline=True)
    rendered = env.from_string(template).render({
        name: _toml_key(value) for name, value in args.items()
    })
    tomllib.loads(rendered)
    return rendered
