"""backfill deployment_revisions.model_definition for legacy NULL rows

Migrations ``25ac68cb28ba`` / ``0a200d0fc480`` wrote ``model_definition
= NULL`` because ``endpoints`` had no resolved value. The post-26.4
agent requires the inlined definition (see ``_load_model_definition``),
so those rows cannot start a session.

Restore non-custom rows from ``runtime_variants.default_model_definition``,
filling ``model_path`` from ``model_mount_destination`` (strict
``ModelConfig`` requires it), resolving the ``{model_path}`` placeholder
in ``start_command``, and stripping explicit ``null`` keys so the
strict ``ModelDefinition`` validator applies its defaults (mirrors the
``exclude_none=True`` dump in ``ModelConfigDraft.to_resolved``).
``custom`` rows are left NULL — repair via
``./bai admin deployment revision refresh``, which re-reads the vfolder
yaml.

Revision ID: 42d912c4bdc6
Revises: 338bc3284f20
Create Date: 2026-05-27

"""

# Part of: 26.4.4

import copy
import json
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "42d912c4bdc6"
down_revision = "338bc3284f20"
branch_labels = None
depends_on = None


def _prune_nulls(obj: Any) -> Any:
    # Strict ``ModelDefinition`` rejects explicit ``null`` for fields that
    # have a non-None default (e.g. ``service.pre_start_actions``,
    # ``service.shell``, every ``ModelHealthCheck`` scalar). The Draft
    # values stored on ``runtime_variants`` carry those nulls, so drop
    # them recursively and let the strict schema's defaults take over.
    if isinstance(obj, dict):
        return {k: _prune_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_prune_nulls(v) for v in obj]
    return obj


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT dr.id, dr.model_mount_destination, rv.default_model_definition "
            "FROM deployment_revisions dr "
            "JOIN runtime_variants rv ON rv.id = dr.runtime_variant_id "
            "WHERE dr.model_definition IS NULL "
            "  AND rv.name != 'custom'"
        )
    ).fetchall()

    for row in rows:
        template = row.default_model_definition or {}
        if not template.get("models"):
            continue
        resolved = copy.deepcopy(template)
        model_path = row.model_mount_destination
        for model in resolved.get("models") or []:
            model["model_path"] = model_path
            service = model.get("service") or {}
            cmd = service.get("start_command")
            if cmd:
                # Replace the placeholder with the actual model path. Usually 'models'
                service["start_command"] = [
                    token.replace("{model_path}", model_path) for token in cmd
                ]
        resolved = _prune_nulls(resolved)
        conn.execute(
            sa.text(
                "UPDATE deployment_revisions "
                "SET model_definition = CAST(:definition AS JSONB) "
                "WHERE id = :id AND model_definition IS NULL"
            ),
            {"definition": json.dumps(resolved), "id": row.id},
        )


def downgrade() -> None:
    # Data-only migration: no-op downgrade.
    pass
