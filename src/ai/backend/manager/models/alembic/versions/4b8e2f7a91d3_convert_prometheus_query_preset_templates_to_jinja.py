"""convert_prometheus_query_preset_templates_to_jinja

The app renders ``query_template`` with Jinja only; the legacy ``str.format``
syntax (``{labels}``, ``{{{labels}}}``, escaped braces) is no longer supported.
This migration rewrites all stored templates, including the seeded defaults, to
the Jinja form. The conversion helpers are a frozen copy of the removed legacy
parsing logic. Idempotent: already-Jinja templates are left untouched.

Revision ID: 4b8e2f7a91d3
Revises: c8d51e7a3b62
Create Date: 2026-08-10 00:00:00.000000

"""

import re
import string

import jinja2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4b8e2f7a91d3"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_BRACE_BLOCK_RE = re.compile(r"\{([^{}]*)\}")


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


def _to_jinja(template: str) -> str:
    """Rewrite a legacy ``str.format`` template as Jinja; other templates unchanged."""
    try:
        parsed = list(string.Formatter().parse(_escape_non_placeholders(template)))
    except ValueError:
        return template
    has_placeholder = False
    for _literal, field, _spec, _conv in parsed:
        if field in ("labels", "window", "group_by"):
            has_placeholder = True
            break
    if not has_placeholder:
        try:
            jinja2.Environment().parse(template)
            return template
        except jinja2.TemplateSyntaxError:
            pass  # legacy escaped braces, e.g. `metric{{job="x"}}` — rebuild as literals
    out = ""
    for literal, field, _spec, _conv in parsed:
        out += literal
        if field is not None:
            if out.endswith("{"):
                # `{` directly before `{{` breaks the Jinja lexer (`{{{` lexes as `{{` + `{`).
                # So we add a space: `metric{` + `{{ labels }}` → `metric{ {{ labels }}`
                out += " "
            out += "{{ " + field + " }}"
    return out


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, query_template FROM prometheus_query_presets")).all()
    for row_id, template in rows:
        converted = _to_jinja(template)
        # Skip if the template is already Jinja or otherwise unchanged by the conversion.
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
