import base64
import secrets
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from .base import GUID, Base, IDColumn

__all__: tuple[str, ...] = ("KeypairRow",)


class KeypairRow(Base):
    __tablename__ = "keypairs"
    id = IDColumn()
    # user_id is nullable to allow creating spare keypairs.
    user_id = sa.Column("user_id", GUID, nullable=True)
    access_key = sa.Column("access_key", sa.String(length=20), unique=True)
    secret_key = sa.Column("secret_key", sa.String(length=40))
    is_active = sa.Column("is_active", sa.Boolean, index=True, server_default=sa.true())
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    modified_at = sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    )
    expired_at = sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True)
    last_used = sa.Column("last_used", sa.DateTime(timezone=True), nullable=True)

    user_row = relationship(
        "UserRow",
        back_populates="keypair_rows",
        primaryjoin="UserRow.uuid == foreign(KeypairRow.user_id)",
    )

    @staticmethod
    def generate_keypair() -> tuple[str, str]:
        """
        AWS-like access key and secret key generation.
        """
        ak = "AKIA" + base64.b32encode(secrets.token_bytes(10)).decode("ascii")
        sk = secrets.token_urlsafe(30)
        return ak, sk

    @classmethod
    async def create_keypair(
        cls, user_id: uuid.UUID, *, db_session: AsyncSession
    ) -> tuple[str, str]:
        ak, sk = cls.generate_keypair()
        await db_session.execute(
            sa.insert(KeypairRow).values(
                user_id=user_id,
                access_key=ak,
                secret_key=sk,
            )
        )
        return ak, sk

    def is_expired(self, current_dt: datetime) -> bool:
        if self.expired_at is None or self.expired_at > current_dt:
            return False
        return True
