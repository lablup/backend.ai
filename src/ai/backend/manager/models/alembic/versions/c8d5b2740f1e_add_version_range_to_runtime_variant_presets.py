"""add version range to runtime_variant_presets

Adds the half-open validity range ``added_version <= v < deprecated_version``, NULL for
every seeded row so a search without the filter is unchanged.

Each bound is also split into the segments the filter and the ordering compare, read
from its leading numeric prefix: 0.9.0rc1 compares as 0.9.0, and what cannot be read
leaves the segments NULL rather than refusing the write.

Revision ID: c8d5b2740f1e
Revises: a7d2c9e41b58
Create Date: 2026-09-07 12:00:00

"""

# Part of: NEXT_RELEASE_VERSION

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c8d5b2740f1e"
down_revision = "a7d2c9e41b58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runtime_variant_presets", sa.Column("added_version", sa.Text(), nullable=True))
    op.add_column(
        "runtime_variant_presets", sa.Column("deprecated_version", sa.Text(), nullable=True)
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column(
            "added_version_major",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN added_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'"
                " THEN (string_to_array(substring(added_version from"
                " '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'), '.')"
                "::int[] || ARRAY[0, 0, 0])[1] END",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column(
            "added_version_minor",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN added_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'"
                " THEN (string_to_array(substring(added_version from"
                " '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'), '.')"
                "::int[] || ARRAY[0, 0, 0])[2] END",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column(
            "added_version_patch",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN added_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'"
                " THEN (string_to_array(substring(added_version from"
                " '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'), '.')"
                "::int[] || ARRAY[0, 0, 0])[3] END",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column(
            "deprecated_version_major",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN deprecated_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'"
                " THEN (string_to_array(substring(deprecated_version from"
                " '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'), '.')"
                "::int[] || ARRAY[0, 0, 0])[1] END",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column(
            "deprecated_version_minor",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN deprecated_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'"
                " THEN (string_to_array(substring(deprecated_version from"
                " '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'), '.')"
                "::int[] || ARRAY[0, 0, 0])[2] END",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column(
            "deprecated_version_patch",
            sa.Integer(),
            sa.Computed(
                "CASE WHEN deprecated_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'"
                " THEN (string_to_array(substring(deprecated_version from"
                " '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'), '.')"
                "::int[] || ARRAY[0, 0, 0])[3] END",
                persisted=True,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("runtime_variant_presets", "deprecated_version_patch")
    op.drop_column("runtime_variant_presets", "deprecated_version_minor")
    op.drop_column("runtime_variant_presets", "deprecated_version_major")
    op.drop_column("runtime_variant_presets", "added_version_patch")
    op.drop_column("runtime_variant_presets", "added_version_minor")
    op.drop_column("runtime_variant_presets", "added_version_major")
    op.drop_column("runtime_variant_presets", "deprecated_version")
    op.drop_column("runtime_variant_presets", "added_version")
