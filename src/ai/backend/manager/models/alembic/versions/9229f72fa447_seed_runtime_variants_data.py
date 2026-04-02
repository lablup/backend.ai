"""seed runtime_variants data

Revision ID: 9229f72fa447
Revises: 2bf0e9a716de
Create Date: 2026-03-31

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9229f72fa447"
down_revision = "2bf0e9a716de"
branch_labels = None
depends_on = None

SEED_DATA = [
    {"name": "vllm", "description": "vLLM"},
    {"name": "nim", "description": "NVIDIA NIM"},
    {"name": "cmd", "description": "Predefined Image Command"},
    {"name": "huggingface-tgi", "description": "Huggingface TGI"},
    {"name": "sglang", "description": "SGLang"},
    {"name": "modular-max", "description": "Modular MAX"},
    {"name": "custom", "description": "Custom (Default)"},
]


def upgrade() -> None:
    for row in SEED_DATA:
        op.execute(
            sa.text(
                "INSERT INTO runtime_variants (name, description) VALUES (:name, :description)"
            ).bindparams(name=row["name"], description=row["description"])
        )


def downgrade() -> None:
    for row in SEED_DATA:
        op.execute(
            sa.text("DELETE FROM runtime_variants WHERE name = :name").bindparams(name=row["name"])
        )
