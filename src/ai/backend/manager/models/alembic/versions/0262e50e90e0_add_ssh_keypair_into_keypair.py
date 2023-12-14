"""add_ssh_keypair_into_keypair

Revision ID: 0262e50e90e0
Revises: 4b7b650bc30e
Create Date: 2019-12-12 07:19:48.052928

"""

import sqlalchemy as sa
from alembic import op
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ai.backend.manager.models.base import convention

# revision identifiers, used by Alembic.
revision = "0262e50e90e0"
down_revision = "4b7b650bc30e"
branch_labels = None
depends_on = None


def generate_ssh_keypair():
    key = rsa.generate_private_key(
        backend=crypto_default_backend(), public_exponent=65537, key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    ).decode("utf-8")
    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
        )
        .decode("utf-8")
    )
    return (public_key, private_key)


def upgrade():
    op.add_column("keypairs", sa.Column("ssh_public_key", sa.String(length=750), nullable=True))
    op.add_column("keypairs", sa.Column("ssh_private_key", sa.String(length=2000), nullable=True))

    # partial table to be preserved and referred
    metadata = sa.MetaData(naming_convention=convention)
    keypairs = sa.Table(
        "keypairs",
        metadata,
        sa.Column("access_key", sa.String(length=20), primary_key=True),
        sa.Column("ssh_public_key", sa.String(length=750), nullable=True),
        sa.Column("ssh_private_key", sa.String(length=2000), nullable=True),
    )

    # Fill in SSH keypairs in every keypairs.
    conn = op.get_bind()
    query = sa.select([keypairs.c.access_key]).select_from(keypairs)
    rows = conn.execute(query).fetchall()
    for row in rows:
        pubkey, privkey = generate_ssh_keypair()
        query = (
            sa.update(keypairs)
            .values(ssh_public_key=pubkey, ssh_private_key=privkey)
            .where(keypairs.c.access_key == row.access_key)
        )
        conn.execute(query)


def downgrade():
    op.drop_column("keypairs", "ssh_public_key")
    op.drop_column("keypairs", "ssh_private_key")
