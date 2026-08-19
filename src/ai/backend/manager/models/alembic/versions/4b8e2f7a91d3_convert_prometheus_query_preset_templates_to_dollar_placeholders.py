"""convert_prometheus_query_preset_templates_to_dollar_placeholders

The app renders ``query_template`` by substituting ``${labels}``, ``${window}``
and ``${group_by}``; every other character is literal PromQL. The legacy
``str.format`` syntax (``{labels}``, ``{{{labels}}}``, escaped braces) is no
longer supported. This migration rewrites all stored templates, including the
seeded defaults, to the new form. The conversion helpers are a frozen copy of
the removed legacy parsing logic. Idempotent: already-converted templates are
left untouched.

Revision ID: 4b8e2f7a91d3
Revises: f1a7c3e9b482
Create Date: 2026-08-10 00:00:00.000000

"""

import re
import string

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4b8e2f7a91d3"
down_revision = "f1a7c3e9b482"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_BRACE_BLOCK_RE = re.compile(r"\{([^{}]*)\}")
_PLACEHOLDER_RE = re.compile(r"\$\{(?:labels|window|group_by)\}")


def _escape_non_placeholders(template: str) -> str:
    """Escape a legacy template so ``str.format`` sees only the three placeholders."""

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        start, end = match.span()
        text = match.string
        already_wrapped = (
            start > 0 and text[start - 1] == "{" and end < len(text) and text[end] == "}"
        )
        inside_escaped_braces = (
            text.rfind("{{", 0, start) > text.rfind("}}", 0, start) and text.find("}}", end) != -1
        )
        if name not in ("labels", "window", "group_by"):
            return match.group(0) if already_wrapped else "{{" + name + "}}"
        if name != "labels":
            return match.group(0)
        return (
            match.group(0)
            if already_wrapped or inside_escaped_braces
            else "{{" + match.group(0) + "}}"
        )

    return _BRACE_BLOCK_RE.sub(repl, template)


def _to_dollar_placeholders(template: str) -> str:
    """Rewrite a legacy ``str.format`` template with ``${...}`` placeholders."""
    if _PLACEHOLDER_RE.search(template):
        return template  # already converted
    try:
        parsed = list(string.Formatter().parse(_escape_non_placeholders(template)))
    except ValueError:
        return template
    out = ""
    for literal, field, _spec, _conv in parsed:
        out += literal
        if field is not None:
            out += "${" + field + "}"
    return out


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, query_template FROM prometheus_query_presets")).all()
    for row_id, template in rows:
        converted = _to_dollar_placeholders(template)
        if converted == template:
            continue
        conn.execute(
            sa.text(
                "UPDATE prometheus_query_presets SET query_template = :template WHERE id = :id"
            ),
            parameters={"template": converted, "id": row_id},
        )


def downgrade() -> None:
    # Data-only migration; the legacy syntax is no longer renderable by the app.
    pass
