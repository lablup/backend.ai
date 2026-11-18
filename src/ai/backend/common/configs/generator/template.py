"""Render a generated sample template into a configuration file."""

from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Mapping

import jinja2
import jinja2.nodes

__all__ = ("render_config_template",)

_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")


def _toml_key(value: str) -> str:
    """Quote a key that is not a TOML bare key, so `local.ssd` stays one key instead of two tables."""
    return value if _BARE_KEY.fullmatch(value) else json.dumps(value, ensure_ascii=False)


def render_config_template(template: str, args: Mapping[str, str]) -> str:
    """Fill the template arguments and check that the result parses as TOML.

    Missing arguments raise ``jinja2.UndefinedError`` naming all of them, and a result that is
    not TOML raises ``tomllib.TOMLDecodeError``, so nothing is written from a half-filled template.
    """
    env = jinja2.Environment(undefined=jinja2.StrictUndefined, keep_trailing_newline=True)
    used = {node.name for node in env.parse(template).find_all(jinja2.nodes.Name)}
    missing = sorted(used - args.keys())
    if missing:
        raise jinja2.UndefinedError(f"missing template arguments: {', '.join(missing)}")
    rendered = env.from_string(template).render({
        name: _toml_key(value) for name, value in args.items()
    })
    tomllib.loads(rendered)
    return rendered
