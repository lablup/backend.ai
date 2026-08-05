"""seed enable-prompt-tokens-details preset for vllm

Adds vLLM's ``--enable-prompt-tokens-details`` flag as a runtime variant
preset so it can be toggled from the model service form instead of the
free-form ``VLLM_EXTRA_ARGS`` escape hatch. With the flag on, vLLM
reports ``usage.prompt_tokens_details`` (notably ``cached_tokens``) in
its OpenAI-compatible responses, which is the only way to observe
whether ``--enable-prefix-caching`` is actually hitting.

The seed migration ``e7b3a1f9c2d4`` already shipped, so the row is added
in a new revision using the same idempotent insert/delete pattern.

Revision ID: fb5befb44035
Revises: c1a7d3f05e28
Create Date: 2026-08-05

"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fb5befb44035"
down_revision = "c1a7d3f05e28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


_PRESET_ROW = {
    "runtime_variant_name": "vllm",
    "name": "enable-prompt-tokens-details",
    "description": "Report prompt token details (e.g. cached tokens) in usage responses.",
    "rank": 2450,
    "preset_target": "args",
    "value_type": "flag",
    "default_value": None,
    "key": "--enable-prompt-tokens-details",
    "category": "monitoring",
    "display_name": "Enable Prompt Tokens Details",
    "ui_option": {
        "ui_type": "checkbox",
    },
}

_INSERT_SQL = sa.text(
    """
    INSERT INTO runtime_variant_presets
        (runtime_variant, name, description, rank, preset_target, value_type,
         default_value, key, category, display_name, ui_option)
    SELECT
        rv.id, :name, :description, :rank, :preset_target, :value_type,
        :default_value, :key, :category, :display_name, CAST(:ui_option AS JSONB)
    FROM runtime_variants rv
    WHERE rv.name = :variant_name
    ON CONFLICT ON CONSTRAINT uq_runtime_variant_presets_variant_name DO NOTHING
    """
)

_DELETE_SQL = sa.text(
    """
    DELETE FROM runtime_variant_presets
    WHERE name = :name
      AND runtime_variant = (SELECT id FROM runtime_variants WHERE name = :variant_name)
    """
)


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        _INSERT_SQL,
        {
            "variant_name": _PRESET_ROW["runtime_variant_name"],
            "name": _PRESET_ROW["name"],
            "description": _PRESET_ROW["description"],
            "rank": _PRESET_ROW["rank"],
            "preset_target": _PRESET_ROW["preset_target"],
            "value_type": _PRESET_ROW["value_type"],
            "default_value": _PRESET_ROW["default_value"],
            "key": _PRESET_ROW["key"],
            "category": _PRESET_ROW["category"],
            "display_name": _PRESET_ROW["display_name"],
            "ui_option": json.dumps(_PRESET_ROW["ui_option"]),
        },
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        _DELETE_SQL,
        {
            "name": _PRESET_ROW["name"],
            "variant_name": _PRESET_ROW["runtime_variant_name"],
        },
    )
