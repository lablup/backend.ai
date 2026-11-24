"""Copy each user's SSH key on keypairs into ssh_keypairs as the default.

The key on the user's default keypair is taken, else the one on their newest keypair. An empty
public key is not copied.
The private key is copied as stored, which ``SecretColumn`` reads as legacy plaintext.
The keypair columns are left in place.
"""

import sqlalchemy as sa
from alembic import op

revision = "ba3e3ab0d354"  # Part of: NEXT_RELEASE_VERSION
down_revision = "019493a701bd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A user already holding a default is skipped, so re-running is a no-op.
    op.execute(
        sa.text("""
        INSERT INTO ssh_keypairs (user_id, public_key, private_key, is_default)
        SELECT DISTINCT ON (kp."user") kp."user", kp.ssh_public_key, kp.ssh_private_key, true
        FROM keypairs AS kp
        WHERE kp.ssh_public_key IS NOT NULL AND kp.ssh_public_key <> ''
          AND NOT EXISTS (
            SELECT 1 FROM ssh_keypairs AS s WHERE s.user_id = kp."user" AND s.is_default
          )
        ORDER BY kp."user", kp.is_default DESC, kp.created_at DESC
    """)
    )


def downgrade() -> None:
    # Write each default back onto every keypair of its user. An encrypted private key
    # cannot be decrypted here, so that user keeps what the keypair columns hold.
    op.execute(
        sa.text("""
        UPDATE keypairs AS kp
        SET ssh_public_key = s.public_key, ssh_private_key = s.private_key
        FROM ssh_keypairs AS s
        WHERE s.user_id = kp."user" AND s.is_default
          AND (s.private_key IS NULL OR s.private_key NOT LIKE 'bai-enc:%')
    """)
    )
    op.execute(sa.text("DELETE FROM ssh_keypairs"))
