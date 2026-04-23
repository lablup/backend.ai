"""add default_model_definition to runtime_variants

Adds an internal-only NOT NULL JSONB column holding each runtime
variant's default ModelDefinition (shaped as ``ModelDefinitionDraft``,
so every inner field stays optional). Values are seeded from what the
per-variant ModelDefinitionGenerators used to emit at runtime;
keeping them in the DB removes the need for name-based dispatch in
Manager. The ``custom`` variant receives an empty Draft since its
definition is loaded from a vfolder at revision-creation time.

Revision ID: b5c6d7e8f9a0
Revises: 7ea9f3c1b2d5
Create Date: 2026-04-19

"""

# Part of: 26.5.0

import json
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "b5c6d7e8f9a0"
down_revision = "7ea9f3c1b2d5"
branch_labels = None
depends_on = None


_COMMON_HEALTH_CHECK = {
    "interval": 10.0,
    "max_retries": 10,
    "initial_delay": 1800.0,
}


def _variant_definition(name: str, port: int, health_path: str | None) -> dict[str, Any]:
    service: dict[str, Any] = {"port": port}
    if health_path is not None:
        service["health_check"] = {"path": health_path, **_COMMON_HEALTH_CHECK}
    return {"models": [{"name": name, "service": service}]}


_EMPTY_DRAFT: dict[str, Any] = {"models": None}


_SEED: dict[str, dict[str, Any]] = {
    "vllm": _variant_definition("vllm-model", 8000, "/health"),
    "sglang": _variant_definition("sglang-model", 9001, "/health"),
    "nim": _variant_definition("nim-model", 8000, "/v1/health/ready"),
    "huggingface-tgi": _variant_definition("tgi-model", 3000, "/info"),
    "modular-max": _variant_definition("max-model", 8000, "/health"),
    "cmd": _variant_definition("image-model", 8000, None),
    "custom": _EMPTY_DRAFT,
}


def upgrade() -> None:
    # Add as nullable so pre-existing rows survive the ALTER; seed next.
    op.add_column(
        "runtime_variants",
        sa.Column("default_model_definition", pgsql.JSONB(), nullable=True),
    )
    for variant_name, definition in _SEED.items():
        op.execute(
            sa.text(
                "UPDATE runtime_variants "
                "SET default_model_definition = CAST(:definition AS JSONB) "
                "WHERE name = :name"
            ).bindparams(name=variant_name, definition=json.dumps(definition))
        )
    # Any row that wasn't covered by the seed (custom variants added by
    # operators) is backfilled with an empty Draft so the NOT NULL alter
    # cannot fail.
    op.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = CAST(:definition AS JSONB) "
            "WHERE default_model_definition IS NULL"
        ).bindparams(definition=json.dumps(_EMPTY_DRAFT))
    )
    op.alter_column("runtime_variants", "default_model_definition", nullable=False)


def downgrade() -> None:
    op.drop_column("runtime_variants", "default_model_definition")
