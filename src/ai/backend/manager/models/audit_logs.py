from __future__ import annotations

import datetime
import enum
import logging
from typing import TYPE_CHECKING, Any, Optional, Sequence
from uuid import UUID

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row

from ai.backend.common.logging import BraceStyleAdapter

from .base import GUID, Base, IDColumn, Item, PaginatedList, StrEnumType
from .minilang.ordering import QueryOrderParser
from .minilang.queryfilter import QueryFilterParser

if TYPE_CHECKING:
    from .gql import GraphQueryContext


log = BraceStyleAdapter(logging.getLogger(__name__))
__all__: Sequence[str] = (
    "AuditLog",
    "AuditLogAction",
    "AuditLogList",
    "AuditLogTargetType",
    "AuditLogRow",
)


class AuditLogAction(str, enum.Enum):
    """AuditLog Action's Enum"""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    PURGE = "PURGE"
    RESTORE = "RESTORE"


class AuditLogTargetType(str, enum.Enum):
    """ """

    USER = "user"
    KEYPAIRS = "keypair"
    GROUP = "group"
    VFOLDER = "vfolder"
    VFOLDER_INVITATION = "vfolder-invitation"
    COMPUTE_SESSION = "compute-session"


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id = IDColumn("id")
    user_id = sa.Column("user_id", GUID, nullable=False)
    access_key = sa.Column("access_key", sa.String(length=20), nullable=False)
    email = sa.Column("email", sa.String(length=64), nullable=False)
    action = sa.Column("action", StrEnumType(AuditLogAction), nullable=False)
    data = sa.Column("data", pgsql.JSONB(), nullable=True)
    target_type = sa.Column(
        "target_type",
        sa.String(length=32),
        nullable=False,
    )
    target = sa.Column("target", sa.String(length=64), nullable=True)
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    success = sa.Column("success", sa.Boolean(), server_default=sa.true(), nullable=False)
    error = sa.Column("error", sa.String(length=128), nullable=True)
    rest_resource = sa.Column("rest_resource", sa.String(length=256), nullable=True)
    gql_query = sa.Column("gql_query", sa.String(length=1024), nullable=True)

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        access_key: str,
        email: str,
        action: AuditLogAction,
        data: dict[str, Any],
        target_type: AuditLogTargetType,
        success: bool,
        *,
        target: str | None = None,
        rest_resource: str | None = None,
        gql_query: str | None = None,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.access_key = access_key
        self.email = email
        self.action = action
        self.data = data
        self.target_type = target_type.value
        self.success = success
        self.target = target
        self.rest_resource = rest_resource
        self.gql_query = gql_query
        self.created_at = datetime.datetime.now()


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
    rest_resource = graphene.String()
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
            rest_resource=row["rest_resource"],
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
                sa.select(AuditLogRow)
                .where((AuditLogRow.email == user_id) | (AuditLogRow.user_id == user_id))
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
                AuditLogRow.created_at.desc(),
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
            .select_from(AuditLogRow)
            .where(
                (AuditLogRow.user_id == user_id) | (AuditLogRow.email == user_id),
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
