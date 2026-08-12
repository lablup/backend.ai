"""seed enable-prompt-tokens-details preset for vllm

Adds vLLM's ``--enable-prompt-tokens-details`` flag as a runtime variant
preset so it can be toggled from the model service form instead of the
free-form ``VLLM_EXTRA_ARGS`` escape hatch. With the flag on, vLLM
reports ``usage.prompt_tokens_details`` (notably ``cached_tokens``) in
its OpenAI-compatible responses, which is the only way to observe
whether ``--enable-prefix-caching`` is actually hitting.

The seed migration ``e7b3a1f9c2d4`` already shipped, so the row is added
in a new revision using the same idempotent insert pattern.

Revision ID: fb5befb44035
Revises: c8d51e7a3b62
Create Date: 2026-08-05

"""

import json
import logging

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fb5befb44035"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")

_VARIANT_NAME = "vllm"

_PRESET_ROW = {
    "name": "enable-prompt-tokens-details",
    "description": "Report prompt token details (e.g. cached tokens) in usage responses.",
    "rank": 3000,
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

_BIND_PARAMS = {
    **_PRESET_ROW,
    "variant_name": _VARIANT_NAME,
    "ui_option": json.dumps(_PRESET_ROW["ui_option"]),
}

_VARIANT_ID_SQL = sa.text("SELECT id FROM runtime_variants WHERE name = :variant_name")

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

# Deployment revisions reference presets through a ``preset_values`` JSONB array
# with no foreign key, so an unguarded delete leaves the reference dangling and
# the argument is dropped without an error at the next reconcile. Matching every
# seeded column additionally keeps a same-named row an operator created out of
# the delete.
_DELETE_SQL = sa.text(
    """
    DELETE FROM runtime_variant_presets rvp
    USING runtime_variants rv
    WHERE rvp.runtime_variant = rv.id
      AND rv.name = :variant_name
      AND rvp.name = :name
      AND rvp.description = :description
      AND rvp.rank = :rank
      AND rvp.preset_target = :preset_target
      AND rvp.value_type = :value_type
      AND rvp.default_value IS NOT DISTINCT FROM CAST(:default_value AS VARCHAR)
      AND rvp.key = :key
      AND rvp.category = :category
      AND rvp.display_name = :display_name
      AND rvp.ui_option = CAST(:ui_option AS JSONB)
      AND NOT EXISTS (
          SELECT 1 FROM deployment_revisions dr
          WHERE dr.preset_values
                @> jsonb_build_array(jsonb_build_object('preset_id', rvp.id::text))
      )
      AND NOT EXISTS (
          SELECT 1 FROM deployment_revision_presets drp
          WHERE drp.preset_values
                @> jsonb_build_array(jsonb_build_object('preset_id', rvp.id::text))
      )
    """
)


def upgrade() -> None:
    conn = op.get_bind()
    if conn.scalar(_VARIANT_ID_SQL, {"variant_name": _VARIANT_NAME}) is None:
        log.warning(
            "runtime variant %r not found; skipped seeding the %r preset",
            _VARIANT_NAME,
            _PRESET_ROW["name"],
        )
        return
    conn.execute(_INSERT_SQL, _BIND_PARAMS)


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(_DELETE_SQL, _BIND_PARAMS)
    if result.rowcount == 0:
        log.warning(
            "kept the %r preset of runtime variant %r: absent, locally modified,"
            " or still referenced by a deployment revision",
            _PRESET_ROW["name"],
            _VARIANT_NAME,
        )
