from __future__ import annotations

from textwrap import dedent


def dedent_strip(text: str) -> str:
    """
    Apply textwrap.dedent and strip to remove both indentation and leading/trailing whitespace.
    This is useful for GraphQL descriptions to ensure clean output in schema introspection.
    """
    return dedent(text).strip()
