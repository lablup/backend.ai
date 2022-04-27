"""change char col to str

Revision ID: 11146ba02235
Revises: 0f7a4b643940
Create Date: 2022-03-25 12:32:05.637628

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql.expression import bindparam

# revision identifiers, used by Alembic.
revision = '11146ba02235'
down_revision = '0f7a4b643940'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    op.alter_column('agents', column_name='architecture', type_=sa.String(length=32))
    query = '''
    UPDATE agents
    SET architecture = TRIM (architecture);
    '''
    conn.execute(query)

def downgrade():
    op.alter_column('agents', column_name='architecture', type_=sa.CHAR(length=32))
