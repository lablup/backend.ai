"""seed start_command in runtime_variants.default_model_definition

PR #11463 added ``start_command`` to the install fixture for vllm /
huggingface-tgi / sglang / modular-max but did not update the seed
migration, and ``populate_fixture`` uses ``ON CONFLICT DO NOTHING`` —
existing rows never received it. Backfill here, preserving any
operator-set value. ``custom`` / ``nim`` / ``cmd`` are intentionally
left as-is (no ``start_command`` in the fixture either).

Revision ID: 338bc3284f20
Revises: b8a85c96607c
Create Date: 2026-05-27

"""

# Part of: 26.4.4

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "338bc3284f20"
down_revision = "b8a85c96607c"
branch_labels = None
depends_on = None


_START_COMMANDS: dict[str, list[str]] = {
    "vllm": ["vllm", "serve", "{model_path}"],
    "huggingface-tgi": ["text-generation-launcher", "--model-id", "{model_path}"],
    "sglang": ["python", "-m", "sglang.launch_server", "--model-path", "{model_path}"],
    "modular-max": ["max", "serve", "--model", "{model_path}"],
}


def upgrade() -> None:
    conn = op.get_bind()
    for variant_name, start_command in _START_COMMANDS.items():
        row = conn.execute(
            sa.text("SELECT default_model_definition FROM runtime_variants WHERE name = :name"),
            {"name": variant_name},
        ).fetchone()
        if row is None or row.default_model_definition is None:
            continue
        definition = row.default_model_definition
        models = definition.get("models") or []
        if not models:
            continue
        service = models[0].setdefault("service", {})
        if service.get("start_command"):
            # Respect operator overrides — never overwrite an existing argv.
            continue
        # Update model definition only if start_command is not already set, to preserve any operator overrides.
        service["start_command"] = start_command
        conn.execute(
            sa.text(
                "UPDATE runtime_variants "
                "SET default_model_definition = CAST(:definition AS JSONB) "
                "WHERE name = :name"
            ),
            {"definition": json.dumps(definition), "name": variant_name},
        )


def downgrade() -> None:
    # Data-only migration: no-op downgrade.
    pass
