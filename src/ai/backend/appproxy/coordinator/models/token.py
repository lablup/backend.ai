from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.appproxy.common.exceptions import ObjectNotFound

from .base import GUID, Base, BaseMixin, IDColumn

__all__ = [
    "Token",
]


class Token(Base, BaseMixin):
    __tablename__ = "tokens"

    id = IDColumn()
    login_session_token = sa.Column(sa.VARCHAR(127), nullable=True)
    kernel_host = sa.Column(sa.VARCHAR(255), nullable=False)
    kernel_port = sa.Column(sa.INTEGER, nullable=False)
    session_id = sa.Column(GUID, nullable=False)
    user_uuid = sa.Column(GUID, nullable=False)
    group_id = sa.Column(GUID, nullable=False)
    access_key = sa.Column(sa.TEXT, nullable=False)
    domain_name = sa.Column(sa.TEXT, nullable=False)

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        token_id: UUID,
    ) -> "Token":
        query = sa.select(Token).where((Token.id == token_id))
        token = await session.scalar(query)
        if not token:
            raise ObjectNotFound(object_name="token")
        return token

    @classmethod
    def create(
        cls,
        id: UUID,
        login_session_token: str | None,
        kernel_host: str,
        kernel_port: int,
        session_id: UUID,
        user_uuid: UUID,
        group_id: UUID,
        access_key: str,
        domain_name: str,
    ) -> "Token":
        t = Token()
        t.id = id
        t.login_session_token = login_session_token
        t.kernel_host = kernel_host
        t.kernel_port = kernel_port
        t.session_id = session_id
        t.user_uuid = user_uuid
        t.group_id = group_id
        t.access_key = access_key
        t.domain_name = domain_name
        return t
