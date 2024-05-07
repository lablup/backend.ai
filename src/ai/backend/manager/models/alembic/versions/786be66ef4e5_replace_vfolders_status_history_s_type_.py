"""Replace vfolders status_history's type map with list

Revision ID: 786be66ef4e5
Revises: 8c8e90aebacd
Create Date: 2024-05-07 05:10:23.799723

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "786be66ef4e5"
down_revision = "8c8e90aebacd"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        WITH data AS (
            SELECT id,
                (jsonb_each(status_history)).key AS status,
                (jsonb_each(status_history)).value AS timestamp
            FROM vfolders
        )
        UPDATE vfolders
        SET status_history = (
            SELECT jsonb_agg(
                jsonb_build_object('status', status, 'timestamp', timestamp)
            )
            FROM data
            WHERE data.id = vfolders.id
        );
    """
    )

    op.execute("UPDATE vfolders SET status_history = '[]'::jsonb WHERE status_history IS NULL;")
    op.alter_column(
        "vfolders",
        "status_history",
        nullable=False,
        default=[],
    )


def downgrade():
    op.execute(
        """
        WITH data AS (
            SELECT id,
                jsonb_object_agg(
                    elem->>'status', elem->>'timestamp'
                ) AS new_status_history
            FROM vfolders,
            jsonb_array_elements(status_history) AS elem
            GROUP BY id
        )
        UPDATE vfolders
        SET status_history = data.new_status_history
        FROM data
        WHERE data.id = vfolders.id;
    """
    )

    op.alter_column("vfolders", "status_history", nullable=True, default=None)
    op.execute("UPDATE vfolders SET status_history = NULL WHERE status_history = '[]'::jsonb;")
