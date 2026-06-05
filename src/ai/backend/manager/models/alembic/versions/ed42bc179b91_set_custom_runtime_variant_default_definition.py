"""seed health-check opt-in defaults for runtime variants

``ModelHealthCheck`` gained an ``enable`` flag (default ``False``), so health
checks are now opt-in. Set up the default model definitions accordingly:

- ``custom`` shipped with an empty definition (``{"models": null}``); seed it
  with a default model whose health check is present but disabled, so a custom
  deployment can opt in later by flipping ``enable``.
- Built-in variants ship a known health_check endpoint and should be checked by
  default; backfill ``enable = true`` on their first model's health check
  (variants without a health_check block, e.g. ``cmd``, are left untouched).

Revision ID: ed42bc179b91
Revises: eb9d9c018e85
Create Date: 2026-05-29

"""

# Part of: 26.6.0

import json
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ed42bc179b91"
down_revision = "eb9d9c018e85"
branch_labels = None
depends_on = None


_CUSTOM_DEFINITION: dict[str, Any] = {
    "models": [
        {
            "name": "custom-model",
            "service": {
                "health_check": {
                    "enable": False,
                    "path": "/health",
                    "interval": 10.0,
                    "max_retries": 10,
                    "initial_delay": 1800.0,
                },
            },
        }
    ]
}

_EMPTY_DEFINITION: dict[str, Any] = {"models": None}


def upgrade() -> None:
    bind = op.get_bind()
    # Seed the empty custom definition with a disabled health check (opt-in baseline).
    bind.execute(
        sa.text(
            "UPDATE runtime_variants SET default_model_definition = CAST(:seed AS JSONB) "
            "WHERE name = 'custom' AND default_model_definition = CAST(:empty AS JSONB)"
        ).bindparams(seed=json.dumps(_CUSTOM_DEFINITION), empty=json.dumps(_EMPTY_DEFINITION))
    )
    # Enable health checks for built-in variants (custom stays opt-in; cmd ships no health check).
    # jsonb_set writes models[0].service.health_check.enable = true, adding the key when absent.
    bind.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = jsonb_set("
            "default_model_definition, '{models,0,service,health_check,enable}', 'true') "
            "WHERE name NOT IN ('custom', 'cmd')"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET default_model_definition = jsonb_set("
            "default_model_definition, '{models,0,service,health_check,enable}', 'false') "
            "WHERE name NOT IN ('custom', 'cmd')"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE runtime_variants SET default_model_definition = CAST(:empty AS JSONB) "
            "WHERE name = 'custom' AND default_model_definition = CAST(:seed AS JSONB)"
        ).bindparams(seed=json.dumps(_CUSTOM_DEFINITION), empty=json.dumps(_EMPTY_DEFINITION))
    )
