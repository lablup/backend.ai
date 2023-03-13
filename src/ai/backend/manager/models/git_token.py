from __future__ import annotations

from typing import Sequence

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime

from .base import Base, metadata

__all__: Sequence[str] = (
    "git_tokens",
    "GitToken",
    "GitTokenRow",
)

git_tokens = sa.Table(
    "git_tokens",
    metadata,
    sa.Column("user_id", sa.String(length=256), index=True, nullable=False, primary_key=True),
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


class GitToken(graphene.ObjectType):
    user_id = graphene.UUID()
    domain = graphene.String()
    token = graphene.String()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()


class GitTokenRow(Base):
    __table__ = git_tokens
