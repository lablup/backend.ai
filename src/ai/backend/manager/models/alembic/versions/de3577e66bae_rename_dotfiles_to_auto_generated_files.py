"""Rename dotfiles to auto_generated_files

Revision ID: de3577e66bae
Revises: 46d84960bae3
Create Date: 2026-11-02 12:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "de3577e66bae"
down_revision = "46d84960bae3"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("dotfiles", "auto_generated_files")
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT pk_dotfiles TO pk_auto_generated_files"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT fk_dotfiles_entity_type_virtual_entities TO fk_auto_generated_files_entity_type_virtual_entities"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT ck_dotfiles_dotfile_perm_length TO ck_auto_generated_files_perm_length"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT ck_dotfiles_dotfile_data_length TO ck_auto_generated_files_data_length"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_file_revisions RENAME CONSTRAINT fk_auto_generated_file_revisions_file_id_dotfiles TO fk_auto_generated_file_revisions_file_id_auto_generated_files"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE organization_auto_generated_file_relations RENAME CONSTRAINT fk_organization_auto_generated_file_relations_file_id_dotfiles TO fk_organization_auto_generated_file_relations_file_id"
        )
    )
    op.execute(
        sa.text("ALTER INDEX uq_dotfiles_is_default RENAME TO uq_auto_generated_files_is_default")
    )


def downgrade() -> None:
    op.execute(
        sa.text("ALTER INDEX uq_auto_generated_files_is_default RENAME TO uq_dotfiles_is_default")
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT pk_auto_generated_files TO pk_dotfiles"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT fk_auto_generated_files_entity_type_virtual_entities TO fk_dotfiles_entity_type_virtual_entities"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT ck_auto_generated_files_perm_length TO ck_dotfiles_dotfile_perm_length"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_files RENAME CONSTRAINT ck_auto_generated_files_data_length TO ck_dotfiles_dotfile_data_length"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE auto_generated_file_revisions RENAME CONSTRAINT fk_auto_generated_file_revisions_file_id_auto_generated_files TO fk_auto_generated_file_revisions_file_id_dotfiles"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE organization_auto_generated_file_relations RENAME CONSTRAINT fk_organization_auto_generated_file_relations_file_id TO fk_organization_auto_generated_file_relations_file_id_dotfiles"
        )
    )
    op.rename_table("auto_generated_files", "dotfiles")
