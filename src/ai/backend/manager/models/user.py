from __future__ import annotations

import enum
import logging
from typing import (
    Any,
    Dict,
    Iterable,
    Optional,
    Sequence,
    TYPE_CHECKING,
)
from uuid import UUID, uuid4

import aiohttp
from dateutil.parser import parse as dtparse
import graphene
from graphene.types.datetime import DateTime as GQLDateTime
from passlib.hash import bcrypt
import sqlalchemy as sa
from sqlalchemy.engine.result import Result
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import (
    AsyncConnection as SAConnection,
    AsyncEngine as SAEngine,
)
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.types import TypeDecorator, VARCHAR

from ai.backend.common import redis
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import RedisConnectionInfo

from ..api.exceptions import VFolderOperationFailed
from .base import (
    EnumValueType,
    IDColumn,
    Item,
    PaginatedList,
    metadata,
    set_if_set,
    batch_result,
    batch_multiresult,
    simple_db_mutate,
    simple_db_mutate_returning_item,
)
from .minilang.queryfilter import QueryFilterParser
from .minilang.ordering import QueryOrderParser
from .storage import StorageSessionManager

if TYPE_CHECKING:
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__file__))


__all__: Sequence[str] = (
    'users',
    'User', 'UserList',
    'UserGroup', 'UserRole',
    'UserInput', 'ModifyUserInput',
    'CreateUser', 'ModifyUser', 'DeleteUser',
    'UserStatus', 'ACTIVE_USER_STATUSES', 'INACTIVE_USER_STATUSES',
)


class PasswordColumn(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        return _hash_password(value)


class UserRole(str, enum.Enum):
    """
    User's role.
    """
    SUPERADMIN = 'superadmin'
    ADMIN = 'admin'
    USER = 'user'
    MONITOR = 'monitor'


class UserStatus(str, enum.Enum):
    """
    User account status.
    """
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DELETED = 'deleted'
    BEFORE_VERIFICATION = 'before-verification'


ACTIVE_USER_STATUSES = (
    UserStatus.ACTIVE,
)

INACTIVE_USER_STATUSES = (
    UserStatus.INACTIVE,
    UserStatus.DELETED,
    UserStatus.BEFORE_VERIFICATION,
)


users = sa.Table(
    'users', metadata,
    IDColumn('uuid'),
    sa.Column('username', sa.String(length=64), unique=True),
    sa.Column('email', sa.String(length=64), index=True,
              nullable=False, unique=True),
    sa.Column('password', PasswordColumn()),
    sa.Column('need_password_change', sa.Boolean),
    sa.Column('full_name', sa.String(length=64)),
    sa.Column('description', sa.String(length=500)),
    sa.Column('status', EnumValueType(UserStatus), default=UserStatus.ACTIVE, nullable=False),
    sa.Column('status_info', sa.Unicode(), nullable=True, default=sa.null()),
    sa.Column('created_at', sa.DateTime(timezone=True),
              server_default=sa.func.now()),
    sa.Column('modified_at', sa.DateTime(timezone=True),
              server_default=sa.func.now(), onupdate=sa.func.current_timestamp()),
    #: Field for synchronization with external services.
    sa.Column('integration_id', sa.String(length=512)),

    sa.Column('domain_name', sa.String(length=64),
              sa.ForeignKey('domains.name'), index=True),
    sa.Column('role', EnumValueType(UserRole), default=UserRole.USER),
)


class UserGroup(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String()

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[UserGroup]:
        if row is None:
            return None
        return cls(
            id=row['id'],
            name=row['name'],
        )

    @classmethod
    async def batch_load_by_user_id(cls, ctx: GraphQueryContext, user_ids: Sequence[UUID]):
        async with ctx.db.begin() as conn:
            from .group import groups, association_groups_users as agus
            j = agus.join(groups, agus.c.group_id == groups.c.id)
            query = (
                sa.select([agus.c.user_id, groups.c.name, groups.c.id])
                .select_from(j)
                .where(agus.c.user_id.in_(user_ids))
            )
            return await batch_multiresult(
                ctx, conn, query, cls,
                user_ids, lambda row: row['user_id'],
            )


class User(graphene.ObjectType):

    class Meta:
        interfaces = (Item, )

    uuid = graphene.UUID()  # legacy
    username = graphene.String()
    email = graphene.String()
    need_password_change = graphene.Boolean()
    full_name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    status = graphene.String()
    status_info = graphene.String()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    role = graphene.String()

    groups = graphene.List(lambda: UserGroup)

    async def resolve_groups(
        self,
        info: graphene.ResolveInfo,
    ) -> Iterable[UserGroup]:
        ctx: GraphQueryContext = info.context
        manager = ctx.dataloader_manager
        loader = manager.get_loader(ctx, 'UserGroup.by_user_id')
        return await loader.load(self.id)

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row,
    ) -> User:
        return cls(
            id=row['uuid'],
            uuid=row['uuid'],
            username=row['username'],
            email=row['email'],
            need_password_change=row['need_password_change'],
            full_name=row['full_name'],
            description=row['description'],
            is_active=True if row['status'] == UserStatus.ACTIVE else False,  # legacy
            status=row['status'],
            status_info=row['status_info'],
            created_at=row['created_at'],
            modified_at=row['modified_at'],
            domain_name=row['domain_name'],
            role=row['role'],
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        group_id: UUID = None,
        is_active: bool = None,
        status: str = None,
        limit: int = None,
    ) -> Sequence[User]:
        """
        Load user's information. Group names associated with the user are also returned.
        """
        if group_id is not None:
            from .group import association_groups_users as agus
            j = (users.join(agus, agus.c.user_id == users.c.uuid))
            query = (
                sa.select([users])
                .select_from(j)
                .where(agus.c.group_id == group_id)
            )
        else:
            query = (
                sa.select([users])
                .select_from(users)
            )
        if ctx.user['role'] != UserRole.SUPERADMIN:
            query = query.where(users.c.domain_name == ctx.user['domain_name'])
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        if limit is not None:
            query = query.limit(limit)
        async with ctx.db.begin_readonly() as conn:
            return [cls.from_row(ctx, row) async for row in (await conn.stream(query))]

    _queryfilter_fieldspec = {
        "uuid": ("uuid", None),
        "username": ("username", None),
        "email": ("email", None),
        "need_password_change": ("need_password_change", None),
        "full_name": ("full_name", None),
        "description": ("description", None),
        "is_active": ("is_active", None),
        "status": ("status", lambda s: UserStatus[s]),
        "status_info": ("status_info", None),
        "created_at": ("created_at", dtparse),
        "modified_at": ("modified_at", dtparse),
        "domain_name": ("domain_name", None),
        "role": ("role", lambda s: UserRole[s]),
    }

    _queryorder_colmap = {
        "uuid": "uuid",
        "username": "username",
        "email": "email",
        "need_password_change": "need_password_change",
        "full_name": "full_name",
        "is_active": "is_active",
        "status": "status",
        "status_info": "status_info",
        "created_at": "created_at",
        "modified_at": "modified_at",
        "domain_name": "domain_name",
        "role": "role",
    }

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        group_id: UUID = None,
        is_active: bool = None,
        status: str = None,
        filter: str = None,
    ) -> int:
        if group_id is not None:
            from .group import association_groups_users as agus
            j = (users.join(agus, agus.c.user_id == users.c.uuid))
            query = (
                sa.select([sa.func.count()])
                .select_from(j)
                .where(agus.c.group_id == group_id)
            )
        else:
            query = (
                sa.select([sa.func.count()])
                .select_from(users)
            )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        if filter is not None:
            if group_id is not None:
                qfparser = QueryFilterParser({
                    k: ('users_' + v[0], v[1])
                    for k, v in cls._queryfilter_fieldspec.items()
                })
            else:
                qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
        return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: str = None,
        group_id: UUID = None,
        is_active: bool = None,
        status: str = None,
        filter: str = None,
        order: str = None,
    ) -> Sequence[User]:
        if group_id is not None:
            from .group import association_groups_users as agus
            j = (users.join(agus, agus.c.user_id == users.c.uuid))
            query = (
                sa.select([users])
                .select_from(j)
                .where(agus.c.group_id == group_id)
                .limit(limit)
                .offset(offset)
            )
        else:
            query = (
                sa.select([users])
                .select_from(users)
                .limit(limit)
                .offset(offset)
            )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        if filter is not None:
            if group_id is not None:
                qfparser = QueryFilterParser({
                    k: ('users_' + v[0], v[1])
                    for k, v in cls._queryfilter_fieldspec.items()
                })
            else:
                qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            if group_id is not None:
                qoparser = QueryOrderParser({
                    k: 'users_' + v
                    for k, v in cls._queryorder_colmap.items()
                })
            else:
                qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(
                users.c.created_at.desc(),
            )
        async with ctx.db.begin_readonly() as conn:
            return [
                cls.from_row(ctx, row) async for row in (await conn.stream(query))
            ]

    @classmethod
    async def batch_load_by_email(
        cls,
        ctx: GraphQueryContext,
        emails: Sequence[str] = None,
        *,
        domain_name: str = None,
        is_active: bool = None,
        status: str = None,
    ) -> Sequence[Optional[User]]:
        if not emails:
            return []
        query = (
            sa.select([users])
            .select_from(users)
            .where(users.c.email.in_(emails))
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx, conn, query, cls,
                emails, lambda row: row['email'],
            )

    @classmethod
    async def batch_load_by_uuid(
        cls,
        ctx: GraphQueryContext,
        user_ids: Sequence[UUID] = None,
        *,
        domain_name: str = None,
        is_active: bool = None,
        status: str = None,
    ) -> Sequence[Optional[User]]:
        if not user_ids:
            return []
        query = (
            sa.select([users])
            .select_from(users)
            .where(users.c.uuid.in_(user_ids))
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if status is not None:
            query = query.where(users.c.status == UserStatus(status))
        elif is_active is not None:  # consider is_active field only if status is empty
            _statuses = ACTIVE_USER_STATUSES if is_active else INACTIVE_USER_STATUSES
            query = query.where(users.c.status.in_(_statuses))
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx, conn, query, cls,
                user_ids, lambda row: row['uuid'],
            )


class UserList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList, )

    items = graphene.List(User, required=True)


class UserInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    password = graphene.String(required=True)
    need_password_change = graphene.Boolean(required=True)
    full_name = graphene.String(required=False, default='')
    description = graphene.String(required=False, default='')
    is_active = graphene.Boolean(required=False, default=True)
    status = graphene.String(required=False, default=UserStatus.ACTIVE)
    domain_name = graphene.String(required=True, default='default')
    role = graphene.String(required=False, default=UserRole.USER)
    group_ids = graphene.List(lambda: graphene.String, required=False)

    # When creating, you MUST set all fields.
    # When modifying, set the field to "None" to skip setting the value.


class ModifyUserInput(graphene.InputObjectType):
    username = graphene.String(required=False)
    password = graphene.String(required=False)
    need_password_change = graphene.Boolean(required=False)
    full_name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    status = graphene.String(required=False)
    domain_name = graphene.String(required=False)
    role = graphene.String(required=False)
    group_ids = graphene.List(lambda: graphene.String, required=False)


class PurgeUserInput(graphene.InputObjectType):
    purge_shared_vfolders = graphene.Boolean(required=False, default=False)


class CreateUser(graphene.Mutation):

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)
        props = UserInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    user = graphene.Field(lambda: User, required=False)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
        props: UserInput,
    ) -> CreateUser:
        graph_ctx: GraphQueryContext = info.context
        username = props.username if props.username else email
        if props.status is None and props.is_active is not None:
            _status = UserStatus.ACTIVE if props.is_active else UserStatus.INACTIVE
        else:
            _status = UserStatus(props.status)
        user_data = {
            'username': username,
            'email': email,
            'password': props.password,
            'need_password_change': props.need_password_change,
            'full_name': props.full_name,
            'description': props.description,
            'status': _status,
            'status_info': 'admin-requested',  # user mutation is only for admin
            'domain_name': props.domain_name,
            'role': UserRole(props.role),
        }
        user_insert_query = (
            sa.insert(users)
            .values(user_data)
        )

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            if result.rowcount == 0:
                return
            created_user = result.first()

            # Create a default keypair for the user.
            from .keypair import CreateKeyPair, keypairs
            kp_data = CreateKeyPair.prepare_new_keypair(
                email,
                graph_ctx.schema.get_type('KeyPairInput').create_container({
                    'is_active': (_status == UserStatus.ACTIVE),
                    'is_admin': (user_data['role'] in [UserRole.SUPERADMIN, UserRole.ADMIN]),
                    'resource_policy': 'default',
                    'rate_limit': 10000,
                }),
            )
            kp_insert_query = (
                sa.insert(keypairs)
                .values(
                    **kp_data,
                    user=created_user.uuid,
                )
            )
            await conn.execute(kp_insert_query)

            # Add user to groups if group_ids parameter is provided.
            from .group import association_groups_users, groups
            if props.group_ids:
                query = (
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == props.domain_name)
                    .where(groups.c.id.in_(props.group_ids))
                )
                grps = (await conn.execute(query)).all()
                if grps:
                    group_data = [
                        {'user_id': created_user.uuid, 'group_id': grp.id}
                        for grp in grps
                    ]
                    group_insert_query = (
                        sa.insert(association_groups_users)
                        .values(group_data)
                    )
                    await conn.execute(group_insert_query)

            return created_user

        return await simple_db_mutate_returning_item(
            cls, graph_ctx, user_insert_query, item_cls=User, post_func=_post_func,
        )


class ModifyUser(graphene.Mutation):

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)
        props = ModifyUserInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    user = graphene.Field(lambda: User)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
        props: ModifyUserInput,
    ) -> ModifyUser:
        graph_ctx: GraphQueryContext = info.context
        data: Dict[str, Any] = {}
        set_if_set(props, data, 'username')
        set_if_set(props, data, 'password')
        set_if_set(props, data, 'need_password_change')
        set_if_set(props, data, 'full_name')
        set_if_set(props, data, 'description')
        set_if_set(props, data, 'status', clean_func=UserStatus)
        set_if_set(props, data, 'domain_name')
        set_if_set(props, data, 'role', clean_func=UserRole)
        if not data and not props.group_ids:
            return cls(ok=False, msg='nothing to update', user=None)
        if data.get('status') is None and props.is_active is not None:
            data['status'] = UserStatus.ACTIVE if props.is_active else UserStatus.INACTIVE

        user_update_data: Dict[str, Any]
        prev_domain_name: str
        prev_role: UserRole

        async def _pre_func(conn: SAConnection) -> None:
            nonlocal user_update_data, prev_domain_name, prev_role
            result = await conn.execute(
                sa.select([
                    users.c.domain_name,
                    users.c.role,
                    users.c.status,
                ])
                .select_from(users)
                .where(users.c.email == email),
            )
            row = result.first()
            prev_domain_name = row.domain_name
            prev_role = row.role
            user_update_data = data.copy()
            if 'status' in data and row.status != data['status']:
                user_update_data['status_info'] = 'admin-requested'  # user mutation is only for admin

        update_query = lambda: (  # uses lambda because user_update_data is modified in _pre_func()
            sa.update(users)
            .values(user_update_data)
            .where(users.c.email == email)
        )

        async def _post_func(conn: SAConnection, result: Result) -> Row:
            nonlocal prev_domain_name, prev_role
            updated_user = result.first()

            if 'role' in data and data['role'] != prev_role:
                from ai.backend.manager.models import keypairs
                result = await conn.execute(
                    sa.select([
                        keypairs.c.user,
                        keypairs.c.is_active,
                        keypairs.c.is_admin,
                    ])
                    .select_from(keypairs)
                    .where(keypairs.c.user == updated_user.uuid)
                    .order_by(sa.desc(keypairs.c.is_admin))
                    .order_by(sa.desc(keypairs.c.is_active)),
                )
                if data['role'] in [UserRole.SUPERADMIN, UserRole.ADMIN]:
                    # User's becomes admin. Set the keypair as active admin.
                    kp = result.first()
                    kp_data = dict()
                    if not kp.is_admin:
                        kp_data['is_admin'] = True
                    if not kp.is_active:
                        kp_data['is_active'] = True
                    if len(kp_data.keys()) > 0:
                        await conn.execute(
                            sa.update(keypairs)
                            .values(kp_data)
                            .where(keypairs.c.user == updated_user.uuid),
                        )
                else:
                    # User becomes non-admin. Make the keypair non-admin as well.
                    # If there are multiple admin keypairs, inactivate them.
                    rows = result.fetchall()
                    cnt = 0
                    kp_updates = []
                    for row in rows:
                        kp_data = {
                            'user': row.user,
                            'is_admin': keypairs.c.is_admin,
                            'is_active': keypairs.c.is_active,
                        }
                        changed = False
                        if cnt == 0:
                            kp_data['is_admin'] = False
                            changed = True
                        elif row.is_admin and row.is_active:
                            kp_data['is_active'] = False
                            changed = True
                        if changed:
                            kp_updates.append(kp_data)
                        cnt += 1
                    await conn.execute(
                        sa.update(keypairs)
                        .values({
                            'is_admin': bindparam('is_admin'),
                            'is_active': bindparam('is_active'),
                        })
                        .where(keypairs.c.user == bindparam('user')),
                        kp_updates,
                    )

            # If domain is changed and no group is associated, clear previous domain's group.
            if prev_domain_name != updated_user.domain_name and not props.group_ids:
                from .group import association_groups_users, groups
                await conn.execute(
                    sa.delete(association_groups_users)
                    .where(association_groups_users.c.user_id == updated_user.uuid),
                )

            # Update user's group if group_ids parameter is provided.
            if props.group_ids and updated_user is not None:
                from .group import association_groups_users, groups  # noqa
                # Clear previous groups associated with the user.
                await conn.execute(
                    sa.delete(association_groups_users)
                    .where(association_groups_users.c.user_id == updated_user.uuid),
                )
                # Add user to new groups.
                result = await conn.execute(
                    sa.select([groups.c.id])
                    .select_from(groups)
                    .where(groups.c.domain_name == updated_user.domain_name)
                    .where(groups.c.id.in_(props.group_ids)),
                )
                grps = result.fetchall()
                if grps:
                    values = [
                        {'user_id': updated_user.uuid, 'group_id': grp.id}
                        for grp in grps
                    ]
                    await conn.execute(
                        sa.insert(association_groups_users).values(values),
                    )

            return updated_user

        return await simple_db_mutate_returning_item(
            cls, graph_ctx, update_query, item_cls=User,
            pre_func=_pre_func, post_func=_post_func,
        )


class DeleteUser(graphene.Mutation):
    """
    Instead of really deleting user, just mark the account as deleted status.

    All related keypairs will also be inactivated.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
    ) -> DeleteUser:
        graph_ctx: GraphQueryContext = info.context

        async def _pre_func(conn: SAConnection) -> None:
            # Make all user keypairs inactive.
            from ai.backend.manager.models import keypairs
            await conn.execute(
                sa.update(keypairs)
                .values(is_active=False)
                .where(keypairs.c.user_id == email),
            )

        update_query = (
            sa.update(users)
            .values(status=UserStatus.DELETED,
                    status_info='admin-requested')
            .where(users.c.email == email)
        )
        return await simple_db_mutate(cls, graph_ctx, update_query, pre_func=_pre_func)


class PurgeUser(graphene.Mutation):
    """
    Delete user as well as all user-related DB informations such as keypairs, kernels, etc.

    If target user has virtual folders, they can be purged together or migrated to the superadmin.

    vFolder treatment policy:
      User-type:
      - vfolder is not shared: delete
      - vfolder is shared:
        + if purge_shared_vfolder is True: delete
        + else: change vfolder's owner to requested admin

    This action cannot be undone.
    """
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        email = graphene.String(required=True)
        props = PurgeUserInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        email: str,
        props: PurgeUserInput,
    ) -> PurgeUser:
        graph_ctx: GraphQueryContext = info.context

        async def _pre_func(conn: SAConnection) -> None:
            user_uuid = await conn.scalar(
                sa.select([users.c.uuid])
                .select_from(users)
                .where(users.c.email == email),
            )
            log.info("Purging all records of the user {0}...", email)

            if await cls.user_vfolder_mounted_to_active_kernels(conn, user_uuid):
                raise RuntimeError(
                    "Some of user's virtual folders are mounted to active kernels. "
                    "Terminate those kernels first.",
                )
            if await cls.user_has_active_kernels(conn, user_uuid):
                raise RuntimeError("User has some active kernels. Terminate them first.")

            if not props.purge_shared_vfolders:
                await cls.migrate_shared_vfolders(
                    conn,
                    deleted_user_uuid=user_uuid,
                    target_user_uuid=graph_ctx.user['uuid'],
                    target_user_email=graph_ctx.user['email'],
                )
            await cls.delete_vfolders(conn, user_uuid, graph_ctx.storage_manager)
            await cls.delete_kernels(conn, user_uuid)
            await cls.delete_keypairs(conn, graph_ctx.redis_stat, user_uuid)

        delete_query = (
            sa.delete(users)
            .where(users.c.email == email)
        )
        return await simple_db_mutate(cls, graph_ctx, delete_query, pre_func=_pre_func)

    @classmethod
    async def migrate_shared_vfolders(
        cls,
        conn: SAConnection,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        """
        Migrate shared virtual folders' ownership to a target user.

        If migrating virtual folder's name collides with target user's already
        existing folder, append random string to the migrating one.

        :param conn: DB connection
        :param deleted_user_uuid: user's UUID who will be deleted
        :param target_user_uuid: user's UUID who will get the ownership of virtual folders

        :return: number of deleted rows
        """
        from . import vfolders, vfolder_invitations, vfolder_permissions
        # Gather target user's virtual folders' names.
        query = (
            sa.select([vfolders.c.name])
            .select_from(vfolders)
            .where(vfolders.c.user == target_user_uuid)
        )
        existing_vfolder_names = [row.name async for row in (await conn.stream(query))]

        # Migrate shared virtual folders.
        # If virtual folder's name collides with target user's folder,
        # append random string to the name of the migrating folder.
        j = vfolder_permissions.join(
            vfolders,
            vfolder_permissions.c.vfolder == vfolders.c.id,
        )
        query = (
            sa.select([vfolders.c.id, vfolders.c.name])
            .select_from(j)
            .where(vfolders.c.user == deleted_user_uuid)
        )
        migrate_updates = []
        async for row in (await conn.stream(query)):
            name = row.name
            if name in existing_vfolder_names:
                name += f'-{uuid4().hex[:10]}'
            migrate_updates.append({'vid': row.id, 'vname': name})
        if migrate_updates:
            # Remove invitations and vfolder_permissions from target user.
            # Target user will be the new owner, and it does not make sense to have
            # invitation and shared permission for its own folder.
            migrate_vfolder_ids = [item['vid'] for item in migrate_updates]
            delete_query = (
                sa.delete(vfolder_invitations)
                .where((vfolder_invitations.c.invitee == target_user_email) &
                       (vfolder_invitations.c.vfolder.in_(migrate_vfolder_ids)))
            )
            await conn.execute(delete_query)
            delete_query = (
                sa.delete(vfolder_permissions)
                .where((vfolder_permissions.c.user == target_user_uuid) &
                       (vfolder_permissions.c.vfolder.in_(migrate_vfolder_ids)))
            )
            await conn.execute(delete_query)

            rowcount = 0
            for item in migrate_updates:
                update_query = (
                    sa.update(vfolders)
                    .values(
                        user=target_user_uuid,
                        name=item['vname'],
                    )
                    .where(vfolders.c.id == item['vid'])
                )
                result = await conn.execute(update_query)
                rowcount += result.rowcount
            if rowcount > 0:
                log.info(
                    "{0} shared folders are detected and migrated to user {1}",
                    rowcount, target_user_uuid,
                )
            return rowcount
        else:
            return 0

    @classmethod
    async def delete_vfolders(
        cls,
        conn: SAConnection,
        user_uuid: UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """
        Delete user's all virtual folders as well as their physical data.

        :param conn: DB connection
        :param user_uuid: user's UUID to delete virtual folders

        :return: number of deleted rows
        """
        from . import vfolders, vfolder_permissions
        await conn.execute(
            vfolder_permissions.delete()
            .where(vfolder_permissions.c.user == user_uuid),
        )
        result = await conn.execute(
            sa.select([vfolders.c.id, vfolders.c.host])
            .select_from(vfolders)
            .where(vfolders.c.user == user_uuid),
        )
        target_vfs = result.fetchall()
        result = await conn.execute(
            sa.delete(vfolders).where(vfolders.c.user == user_uuid),
        )
        for row in target_vfs:
            try:
                async with storage_manager.request(
                    row['host'], 'POST', 'folder/delete',
                    json={
                        'volume': storage_manager.split_host(row['host'])[1],
                        'vfid': str(row['id']),
                    },
                    raise_for_status=True,
                ):
                    pass
            except aiohttp.ClientResponseError:
                log.error('error on deleting vfolder filesystem directory: {0}', row['id'])
                raise VFolderOperationFailed
        if result.rowcount > 0:
            log.info('deleted {0} user\'s virtual folders ({1})', result.rowcount, user_uuid)
        return result.rowcount

    @classmethod
    async def user_vfolder_mounted_to_active_kernels(
        cls,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if no active kernel is using the user's virtual folders.

        :param conn: DB connection
        :param user_uuid: user's UUID

        :return: True if a virtual folder is mounted to active kernels.
        """
        from . import kernels, vfolders, AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES
        result = await conn.execute(
            sa.select([vfolders.c.id])
            .select_from(vfolders)
            .where(vfolders.c.user == user_uuid),
        )
        rows = result.fetchall()
        user_vfolder_ids = [row.id for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        async for row in (await conn.stream(query)):
            for _mount in row['mounts']:
                try:
                    vfolder_id = UUID(_mount[2])
                    if vfolder_id in user_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    @classmethod
    async def user_has_active_kernels(
        cls,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if the user does not have active kernels.

        :param conn: DB connection
        :param user_uuid: user's UUID

        :return: True if the user has some active kernels.
        """
        from . import kernels, AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES
        active_kernel_count = await conn.scalar(
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(
                (kernels.c.user_uuid == user_uuid) &
                (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            ),
        )
        return (active_kernel_count > 0)

    @classmethod
    async def delete_kernels(
        cls,
        conn: SAConnection,
        user_uuid: UUID,
    ) -> int:
        """
        Delete user's all kernels.

        :param conn: DB connection
        :param user_uuid: user's UUID to delete kernels
        :return: number of deleted rows
        """
        from . import kernels
        result = await conn.execute(
            sa.delete(kernels)
            .where(kernels.c.user_uuid == user_uuid),
        )
        if result.rowcount > 0:
            log.info('deleted {0} user\'s kernels ({1})', result.rowcount, user_uuid)
        return result.rowcount

    @classmethod
    async def delete_keypairs(
        cls,
        conn: SAConnection,
        redis_conn: RedisConnectionInfo,
        user_uuid: UUID,
    ) -> int:
        """
        Delete user's all keypairs.

        :param conn: DB connection
        :param redis_conn: redis connection info
        :param user_uuid: user's UUID to delete keypairs
        :return: number of deleted rows
        """
        from . import keypairs
        ak_rows = await conn.execute(
            sa.select([keypairs.c.access_key])
            .where(keypairs.c.user == user_uuid),
        )
        access_key = ak_rows.first().access_key
        await redis.execute(
            redis_conn,
            lambda r: r.delete(f'keypair.concurrency_used.{access_key}'),
        )
        result = await conn.execute(
            sa.delete(keypairs)
            .where(keypairs.c.user == user_uuid),
        )
        if result.rowcount > 0:
            log.info('deleted {0} user\'s keypairs ({1})', result.rowcount, user_uuid)
        return result.rowcount


def _hash_password(password):
    return bcrypt.using(rounds=12).hash(password)


def _verify_password(guess, hashed):
    return bcrypt.verify(guess, hashed)


async def check_credential(
    db: SAEngine,
    domain: str,
    email: str,
    password: str,
) -> Any:
    async with db.begin_readonly() as conn:
        result = await conn.execute(
            sa.select([users])
            .select_from(users)
            .where(
                (users.c.email == email) &
                (users.c.domain_name == domain),
            ),
        )
    row = result.first()
    if row is None:
        return None
    if row['password'] is None:
        # user password is not set.
        return None
    try:
        if _verify_password(password, row['password']):
            return row
    except ValueError:
        return None
    return None
