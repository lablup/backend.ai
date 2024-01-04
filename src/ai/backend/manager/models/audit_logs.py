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

from .base import EnumValueType, Item, PaginatedList, metadata, simple_db_mutate
from .minilang.ordering import QueryOrderParser
from .minilang.queryfilter import QueryFilterParser
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext
log = BraceStyleAdapter(logging.getLogger(__name__))
__all__: Sequence[str] = (
    "audit_logs",
    "AuditLog",
    "AuditLogList",
    "AuditLogInput",
    "CreateAuditLog",
)


class AuditLogAction(str, enum.Enum):
    """AuditLog Action's Enum"""

    CREATE = "CREATE"
    CHANGE = "CHANGE"
    DELETE = "DELETE"


class AuditLogTargetType(str, enum.Enum):
    """ """

    USER = "user"
    KEYS = "keypairs"
    VFOLDER = "vfolder"


audit_logs = sa.Table(
    "audit_logs",
    metadata,
    sa.Column("user_id", sa.String(length=256), index=True, nullable=False),
    sa.Column("access_key", sa.String(length=20), index=True, nullable=False),
    sa.Column("email", sa.String(length=64), index=True, nullable=False),
    sa.Column("action", EnumValueType(AuditLogAction), index=True, nullable=False),
    sa.Column("data", pgsql.JSONB(), nullable=True),
    sa.Column(
        "target_type",
        EnumValueType(AuditLogTargetType),
        index=True,
        nullable=False,
    ),
    sa.Column("target", sa.String(length=64), index=True, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    sa.Column("success", sa.Boolean(), server_default=sa.true(), index=True, nullable=False),
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
        )

    _queryfilter_fieldspec = {
        "user_id": ("user_id", None),
        "email": ("email", None),
        "access_key": ("access_key", None),
        "action": ("action", None),
        "target_type": ("target_type", None),
        "target": ("target", None),
        "created_at": ("created_at", dtparse),
    }

    _queryorder_colmap = {
        "user_id": "user_id",
        "access_key": "access_key",
        "email": "email",
        "action": "action",
        "target_type": "target_type",
        "target": "target",
        "created_at": "created_at",
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


class AuditLogInput(graphene.InputObjectType):
    user_email = graphene.String(required=True)
    user_id = graphene.String(required=True)
    access_key = graphene.String(required=True)
    data_before = graphene.JSONString(required=True)
    data_after = graphene.JSONString(required=True)
    action = graphene.String(required=True)
    target_type = graphene.String(required=True)
    target = graphene.String(required=True)


class CreateAuditLog(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        props = AuditLogInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    audit_logs = graphene.Field(lambda: AuditLog, required=False)

    @classmethod
    async def mutate(
        cls,
        # root,
        info: graphene.ResolveInfo,
        props: AuditLogInput,
    ) -> CreateAuditLog:
        graph_ctx: GraphQueryContext = info.context
        if props["action"] == "CHANGE":
            prepare_data_before = {}
            prepare_data_after = {}
            for key in props[
                "data_after"
            ].keys():  # check update command options to only show changes
                value = props["data_after"][key]
                if props["data_before"][key] != value and value is not None:
                    if key == "password":
                        # don't show new password
                        prepare_data_after.update({key: "new_password_set"})
                    else:
                        prepare_data_after.update({key: value})
            for key in prepare_data_after.keys():
                prepare_data_before.update({key: props["data_before"][key]})
        else:
            prepare_data_before = props["data_before"]
            prepare_data_after = props["data_after"]
        data_set = {
            "user_id": str(props["user_id"]),
            "access_key": props["access_key"],
            "email": props["user_email"],
            "action": props["action"],
            "target_type": props["target_type"],
            "target": str(props["target"]),
            "data": {
                "before": prepare_data_before,
                "after": prepare_data_after,
            },
        }
        if prepare_data_after or prepare_data_before:
            insert_query = sa.insert(audit_logs).values(data_set)
        else:
            log.warning("No data to write in Audit log")
            insert_query = ()
        return await simple_db_mutate(cls, graph_ctx, insert_query)
