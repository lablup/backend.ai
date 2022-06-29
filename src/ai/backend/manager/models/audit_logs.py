from __future__ import annotations


import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from .base import (
    metadata, Item,
    PaginatedList,
    simple_db_mutate)
from typing import (
    Sequence,
    Optional,
    TYPE_CHECKING)
import logging
from .user import UserRole

from graphene.types.datetime import DateTime as GQLDateTime
import graphene

from ai.backend.common.logging import BraceStyleAdapter


if TYPE_CHECKING:
    from .gql import GraphQueryContext
log = BraceStyleAdapter(logging.getLogger(__name__))
__all__: Sequence[str] = (
    'audit_logs',
    'AuditLog', 'AuditLogList', 'AuditLogInput',
    'CreateAuditLog',


)

audit_logs = sa.Table(
    'audit_logs', metadata,

    sa.Column('user_id', sa.String(length=256), index=True),
    sa.Column('access_key', sa.String(length=20), index=True),
    sa.Column('email', sa.String(length=64), index=True),
    sa.Column('action', sa.Enum('CREATE', 'CHANGE', 'DELETE',
              name='auditlogs_action', create_type=False), index=True),
    sa.Column('data', pgsql.JSONB()),
    sa.Column('target', sa.String(length=64), index=True),
    sa.Column('created_at', sa.DateTime(timezone=True),
                server_default=sa.func.now(), index=True),
)


class AuditLog(graphene.ObjectType):
    class Meta:
        interfaces = (Item, )

    user_id = graphene.String()
    access_key = graphene.String()
    email = graphene.String()
    action = graphene.String()
    data = graphene.JSONString()
    target = graphene.String()
    created_at = GQLDateTime()

    @classmethod
    def from_row(cls,
                 ctx: GraphQueryContext,
                 row: Row,
                 ) -> Optional[AuditLog]:
        if row is None:
            return None
        return cls(
            user_id=row['user_id'],
            access_key=row['access_key'],
            email=row['email'],
            action=row['action'],
            data=row['data'],
            target=row['target'],
            created_at=row['created_at'],

        )

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        user_id: str = None,
    ) -> Sequence[AuditLog]:
        """
        Load Audit Logs
        """

        if user_id is not None:
            query = (
                sa.select([audit_logs])
                .select_from(audit_logs)
                .where(audit_logs.c.user_id == user_id)
                .limit(limit)
                .offset(offset)
            )

        async with ctx.db.begin_readonly() as conn:
            b = [
                obj async for row in (await conn.stream(query))
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
                audit_logs.c.user_id == user_id,
            )

        )
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()


class AuditLogList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList, )

    items = graphene.List(AuditLog, required=True)


class AuditLogInput(graphene.InputObjectType):
    user_email = graphene.String(required=True)
    user_id = graphene.String(required=True)
    access_key = graphene.String(required=True)
    data_before = graphene.JSONString(required=True)
    data_after = graphene.JSONString(required=True)
    action = graphene.String(required=True)
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
        if props['action'] == 'CHANGE':
            prepare_data_before = {}
            prepare_data_after = {}
            for key in props['data_after'].keys():  # check update command options to only show changes
                value = props['data_after'][key]
                if props['data_before'][key] != value and value is not None:
                    if key == 'password':
                        prepare_data_after.update({key: 'new_password_set'})  # don't show new password
                    else:
                        prepare_data_after.update({key: value})
            for key in prepare_data_after.keys():
                prepare_data_before.update({key: props['data_before'][key]})
        else:
            prepare_data_before = props['data_before']
            prepare_data_after = props['data_after']
        data_set = {
            'user_id': str(props['user_id']),
            'access_key': props['access_key'],
            'email': props['user_email'],
            'action': props['action'],
            'target': str(props['target']),
            'data': {
                'before':
                    prepare_data_before,
                'after':
                    prepare_data_after,
            },
        }
        if prepare_data_after or prepare_data_before:
            insert_query = (
                sa.insert(audit_logs)
                .values(data_set)
            )
        else:
            log.warning("No data to write in Audit log")
            insert_query = ()
        return await simple_db_mutate(cls, graph_ctx, insert_query)
