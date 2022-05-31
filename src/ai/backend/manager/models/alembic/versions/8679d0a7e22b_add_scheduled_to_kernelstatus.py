"""add-scheduled-to-kernelstatus

Revision ID: 8679d0a7e22b
Revises: 518ecf41f567
Create Date: 2021-04-01 14:24:27.885209

"""
import textwrap

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8679d0a7e22b'
down_revision = '518ecf41f567'
branch_labels = None
depends_on = None

kernelstatus_new_values = [
    'PENDING',
    'SCHEDULED',  # added
    'PREPARING',
    'BUILDING',
    'PULLING',
    'RUNNING',
    'RESTARTING',
    'RESIZING',
    'SUSPENDED',
    'TERMINATING',
    'TERMINATED',
    'ERROR',
    'CANCELLED',
]
kernelstatus_new = postgresql.ENUM(*kernelstatus_new_values, name='kernelstatus')

kernelstatus_old_values = [
    'PENDING',
    'PREPARING',
    'BUILDING',
    'PULLING',
    'RUNNING',
    'RESTARTING',
    'RESIZING',
    'SUSPENDED',
    'TERMINATING',
    'TERMINATED',
    'ERROR',
    'CANCELLED',
]
kernelstatus_old = postgresql.ENUM(*kernelstatus_old_values, name='kernelstatus')


def upgrade():
    conn = op.get_bind()
    conn.execute('DROP INDEX IF EXISTS ix_kernels_unique_sess_token;')
    conn.execute('ALTER TYPE kernelstatus RENAME TO kernelstatus_old;')
    kernelstatus_new.create(conn)
    conn.execute(textwrap.dedent('''\
    ALTER TABLE kernels
        ALTER COLUMN "status" DROP DEFAULT,
        ALTER COLUMN "status" TYPE kernelstatus USING "status"::text::kernelstatus,
        ALTER COLUMN "status" SET DEFAULT 'PENDING'::kernelstatus;
    DROP TYPE kernelstatus_old;
    '''))
    # This also fixes the unique constraint columns:
    #   (access_key, session_id) -> (access_key, session_name)
    op.create_index(
        'ix_kernels_unique_sess_token', 'kernels', ['access_key', 'session_name'],
        unique=True, postgresql_where=sa.text(
            "status NOT IN ('TERMINATED', 'CANCELLED') and cluster_role = 'main'"
        ))


def downgrade():
    op.drop_index('ix_kernels_unique_sess_token', table_name='kernels')
    conn = op.get_bind()
    conn.execute('ALTER TYPE kernelstatus RENAME TO kernelstatus_new;')
    kernelstatus_old.create(conn)
    conn.execute(textwrap.dedent('''\
    ALTER TABLE kernels
        ALTER COLUMN "status" DROP DEFAULT,
        ALTER COLUMN "status" TYPE kernelstatus USING (
            CASE "status"::text
                WHEN 'SCHEDULED' THEN 'PREPARING'
                ELSE "status"::text
            END
        )::kernelstatus,
        ALTER COLUMN "status" SET DEFAULT 'PENDING'::kernelstatus;
    DROP TYPE kernelstatus_new;
    '''))
    op.create_index(
        'ix_kernels_unique_sess_token', 'kernels', ['access_key', 'session_id'],
        unique=True, postgresql_where=sa.text(
            "status != 'TERMINATED' and cluster_role = 'main'"
        ))
