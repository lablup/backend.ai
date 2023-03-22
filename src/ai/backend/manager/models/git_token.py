from __future__ import annotations

import json
import logging
import uuid
from typing import Sequence

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common.logging import BraceStyleAdapter

from .base import GUID, Base, metadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


__all__: Sequence[str] = (
    "git_tokens",
    "GitToken",
    "GitTokenRow",
    "insert_update_git_tokens",
)

git_tokens = sa.Table(
    "git_tokens",
    metadata,
    sa.Column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column("domain", sa.String(length=200), unique=True, primary_key=True, nullable=False),
    sa.Column("token", sa.String(length=200)),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    ),
)


async def insert_update_git_tokens(
    conn: SAConnection, user_uuid: uuid.UUID, token_list_str: str
) -> None:
    token_list = json.loads(token_list_str)
    domain_list = []
    # check domain_list
    for key, value in token_list.items():
        domain_list.append(key)
    # delete some non-exist key on domain list
    delete_stmt = sa.delete(git_tokens).where(
        sa.and_(git_tokens.c.user_id == user_uuid), sa.not_(git_tokens.c.domain.in_(domain_list))
    )
    await conn.execute(delete_stmt)

    for key, value in token_list.items():
        data = {"user_id": user_uuid, "domain": key, "token": value}
        query = insert(git_tokens).values(data)
        query = query.on_conflict_do_update(
            index_elements=["user_id", "domain"], set_=dict(token=query.excluded.token)
        )
        await conn.execute(query)

    await conn.commit()


class GitToken(graphene.ObjectType):
    user_id = graphene.UUID()
    domain = graphene.String()
    token = graphene.String()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()


class GitTokenRow(Base):
    __table__ = git_tokens
