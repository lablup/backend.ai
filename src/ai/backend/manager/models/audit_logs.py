from __future__ import annotations

import enum
import logging
from typing import TYPE_CHECKING, Optional, Sequence

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row

from ai.backend.common.logging import BraceStyleAdapter

from .base import EnumValueType, Item, PaginatedList, metadata
from .minilang.ordering import QueryOrderParser
from .minilang.queryfilter import QueryFilterParser

if TYPE_CHECKING:
    from .gql import GraphQueryContext


log = BraceStyleAdapter(logging.getLogger(__name__))
__all__: Sequence[str] = (
    "audit_logs",
    "AuditLog",
    "AuditLogList",
)


class AuditLogAction(str, enum.Enum):
    """AuditLog Action's Enum"""

    CREATE = "CREATE"
    CHANGE = "CHANGE"
    DELETE = "DELETE"
    PURGE = "PURGE"


class AuditLogTargetType(str, enum.Enum):
    """ """

    USER = "user"
    KEYPAIRS = "keypair"
    GROUP = "group"
    VFOLDER = "vfolder"
    COMPUTE_SESSION = "compute-session"


audit_logs = sa.Table(
    "audit_logs",
    metadata,
    sa.Column("user_id", sa.String(length=256), nullable=False),
    sa.Column("access_key", sa.String(length=20), nullable=False),
    sa.Column("email", sa.String(length=64), nullable=False),
    sa.Column("action", EnumValueType(AuditLogAction), nullable=False),
    sa.Column("data", pgsql.JSONB(), nullable=True),
    sa.Column(
        "target_type",
        EnumValueType(AuditLogTargetType),
        index=True,
        nullable=False,
    ),
    sa.Column("target", sa.String(length=64), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    sa.Column("success", sa.Boolean(), server_default=sa.true(), nullable=False),
    sa.Column("rest_api_path", sa.String(length=256), nullable=True),
    sa.Column("gql_query", sa.String(length=256), nullable=True),
)


class AuditLog(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    user_id = graphene.String()
    access_key = graphene.String()
    email = graphene.String()
    action = graphene.String()
    data = graphene.JSONString()
    target_type = graphene.String()
    target = graphene.String()
    created_at = GQLDateTime()
    rest_api_path = graphene.String()
    gql_query = graphene.String()

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row,
    ) -> Optional[AuditLog]:
        if row is None:
            return None
        return cls(
            user_id=row["user_id"],
            access_key=row["access_key"],
            email=row["email"],
            action=row["action"],
            data=row["data"],
            target_type=row["target_type"],
            target=row["target"],
            created_at=row["created_at"],
            rest_api_path=row["rest_api_path"],
            gql_query=row["gql_query"],
        )

    _queryfilter_fieldspec = {
        "user_id": ("user_id", None),
        "email": ("email", None),
        "access_key": ("access_key", None),
        "action": ("action", None),
        "target_type": ("target_type", None),
        "target": ("target", None),
        "created_at": ("created_at", dtparse),
        "rest_api": ("rest_api", None),
        "gql_query": ("gql_query", None),
    }

    _queryorder_colmap = {
        "user_id": ("user_id", None),
        "access_key": ("access_key", None),
        "email": ("email", None),
        "action": ("action", None),
        "target_type": ("target_type", None),
        "target": ("target", None),
        "created_at": ("created_at", None),
        "rest_api": ("rest_api", None),
        "gql_query": ("gql_query", None),
    }

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        user_id: str = None,
        filter: str = None,
        order: str = None,
    ) -> Sequence[AuditLog]:
        """
        Load Audit Logs
        """

        if user_id is not None:
            query = (
                sa.select([audit_logs])
                .select_from(audit_logs)
                .where((audit_logs.c.email == user_id) | (audit_logs.c.user_id == user_id))
                .limit(limit)
                .offset(offset)
            )
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(
                audit_logs.c.created_at.desc(),
            )
        async with ctx.db.begin_readonly() as conn:
            b = [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]
            return b

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        user_id: str = None,
        filter: str = None,
    ) -> int:
        query = (
            sa.select([sa.func.count()])
            .select_from(audit_logs)
            .where(
                (audit_logs.c.user_id == user_id) | (audit_logs.c.email == user_id),
            )
        )
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()


class AuditLogList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(AuditLog, required=True)
