"""Replace status_history's type map with list

Revision ID: 37fb8b8e98e5
Revises: 8c74e7df26f8
Create Date: 2023-10-30 08:02:27.845105

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "37fb8b8e98e5"
down_revision = "8c74e7df26f8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        WITH data AS (
            SELECT id,
                   (jsonb_each(status_history)).key,
                   (jsonb_each(status_history)).value
            FROM kernels
        )
        UPDATE kernels
        SET status_history = (
            SELECT jsonb_agg(
                jsonb_build_array(key, value)
            )
            FROM data
            WHERE data.id = kernels.id
        );
    """)

    op.execute("""
        WITH data AS (
            SELECT id,
                   (jsonb_each(status_history)).key,
                   (jsonb_each(status_history)).value
            FROM sessions
        )
        UPDATE sessions
        SET status_history = (
            SELECT jsonb_agg(
                jsonb_build_array(key, value)
            )
            FROM data
            WHERE data.id = sessions.id
        );
    """)


def downgrade():
    op.execute("""
        WITH data AS (
            SELECT id, jsonb_object_agg(
                elem->>0, elem->>1
            ) AS new_status_history
            FROM kernels,
            jsonb_array_elements(status_history) AS elem
            GROUP BY id
        )
        UPDATE kernels
        SET status_history = data.new_status_history
        FROM data
        WHERE data.id = kernels.id;
    """)

    op.execute("""
        WITH data AS (
            SELECT id, jsonb_object_agg(
                elem->>0, elem->>1
            ) AS new_status_history
            FROM sessions,
            jsonb_array_elements(status_history) AS elem
            GROUP BY id
        )
        UPDATE sessions
        SET status_history = data.new_status_history
        FROM data
        WHERE data.id = sessions.id;
    """)
