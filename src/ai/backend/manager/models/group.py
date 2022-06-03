from __future__ import annotations

import asyncio
import logging
import re
from typing import (
    Any,
    Dict,
    Optional,
    Sequence, TYPE_CHECKING,
    TypedDict,
    Union,
)
import uuid

import aiohttp
import graphene
from graphene.types.datetime import DateTime as GQLDateTime
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common import msgpack
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import ResourceSlot

from ..api.exceptions import VFolderOperationFailed
from ..defs import RESERVED_DOTFILES
from .base import (
    metadata, GUID, IDColumn, ResourceSlotColumn,
    privileged_mutation,
    set_if_set,
    simple_db_mutate,
    simple_db_mutate_returning_item,
    batch_result,
    batch_multiresult,
)
from .storage import StorageSessionManager
from .user import ModifyUserInput, UserRole
from .utils import execute_with_retry

if TYPE_CHECKING:
    from .gql import GraphQueryContext
    from .scaling_group import ScalingGroup

log = BraceStyleAdapter(logging.getLogger(__file__))


__all__: Sequence[str] = (
    'groups', 'association_groups_users',
    'resolve_group_name_or_id',
    'Group', 'GroupInput', 'ModifyGroupInput',
    'CreateGroup', 'ModifyGroup', 'DeleteGroup',
    'GroupDotfile', 'MAXIMUM_DOTFILE_SIZE',
    'query_group_dotfiles',
    'query_group_domain',
    'verify_dotfile_name',
)

MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB
_rx_slug = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$')

association_groups_users = sa.Table(
    'association_groups_users', metadata,
    sa.Column('user_id', GUID,
              sa.ForeignKey('users.uuid', onupdate='CASCADE', ondelete='CASCADE'),
              nullable=False),
    sa.Column('group_id', GUID,
              sa.ForeignKey('groups.id', onupdate='CASCADE', ondelete='CASCADE'),
              nullable=False),
    sa.UniqueConstraint('user_id', 'group_id', name='uq_association_user_id_group_id'),
)


groups = sa.Table(
    'groups', metadata,
    IDColumn('id'),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=512)),
    sa.Column('is_active', sa.Boolean, default=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column('modified_at', sa.DateTime(timezone=True),
              server_default=sa.func.now(), onupdate=sa.func.current_timestamp()),
    #: Field for synchronization with external services.
    sa.Column('integration_id', sa.String(length=512)),

    sa.Column('domain_name', sa.String(length=64),
              sa.ForeignKey('domains.name', onupdate='CASCADE', ondelete='CASCADE'),
              nullable=False, index=True),
    # TODO: separate resource-related fields with new domain resource policy table when needed.
    sa.Column('total_resource_slots', ResourceSlotColumn(), default='{}'),
    sa.Column('allowed_vfolder_hosts', pgsql.ARRAY(sa.String), nullable=False, default='{}'),
    sa.UniqueConstraint('name', 'domain_name', name='uq_groups_name_domain_name'),
    # dotfiles column, \x90 means empty list in msgpack
    sa.Column('dotfiles', sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b'\x90'),
)


async def resolve_group_name_or_id(
    db_conn: SAConnection,
    domain_name: str,
    value: Union[str, uuid.UUID],
) -> Optional[uuid.UUID]:
    if isinstance(value, str):
        query = (
            sa.select([groups.c.id])
            .select_from(groups)
            .where(
                (groups.c.name == value) &
                (groups.c.domain_name == domain_name),
            )
        )
        return await db_conn.scalar(query)
    elif isinstance(value, uuid.UUID):
        query = (
            sa.select([groups.c.id])
            .select_from(groups)
            .where(
                (groups.c.id == value) &
                (groups.c.domain_name == domain_name),
            )
        )
        return await db_conn.scalar(query)
    else:
        raise TypeError('unexpected type for group_name_or_id')


class Group(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    created_at = GQLDateTime()
    modified_at = GQLDateTime()
    domain_name = graphene.String()
    total_resource_slots = graphene.JSONString()
    allowed_vfolder_hosts = graphene.List(lambda: graphene.String)
    integration_id = graphene.String()

    scaling_groups = graphene.List(lambda: graphene.String)

    @classmethod
    def from_row(cls, graph_ctx: GraphQueryContext, row: Row) -> Optional[Group]:
        if row is None:
            return None
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            modified_at=row['modified_at'],
            domain_name=row['domain_name'],
            total_resource_slots=row['total_resource_slots'].to_json(),
            allowed_vfolder_hosts=row['allowed_vfolder_hosts'],
            integration_id=row['integration_id'],
        )

    async def resolve_scaling_groups(self, info: graphene.ResolveInfo) -> Sequence[ScalingGroup]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(
            graph_ctx, "ScalingGroup.by_group",
        )
        sgroups = await loader.load(self.id)
        return [sg.name for sg in sgroups]

    @classmethod
    async def load_all(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        is_active: bool = None,
    ) -> Sequence[Group]:
        query = (
            sa.select([groups])
            .select_from(groups)
        )
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if is_active is not None:
            query = query.where(groups.c.is_active == is_active)
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_id(
        cls,
        graph_ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
        *,
        domain_name: str = None,
    ) -> Sequence[Group | None]:
        query = (
            sa.select([groups])
            .select_from(groups)
            .where(groups.c.id.in_(group_ids))
        )
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_result(
                graph_ctx, conn, query, cls,
                group_ids, lambda row: row['id'],
            )

    @classmethod
    async def batch_load_by_name(
        cls,
        graph_ctx: GraphQueryContext,
        group_names: Sequence[str],
        *,
        domain_name: str = None,
    ) -> Sequence[Sequence[Group | None]]:
        query = (
            sa.select([groups])
            .select_from(groups)
            .where(groups.c.name.in_(group_names))
        )
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx, conn, query, cls,
                group_names, lambda row: row['name'],
            )

    @classmethod
    async def batch_load_by_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[Group | None]]:
        j = sa.join(
            groups, association_groups_users,
            groups.c.id == association_groups_users.c.group_id,
        )
        query = (
            sa.select([groups, association_groups_users.c.user_id])
            .select_from(j)
            .where(association_groups_users.c.user_id.in_(user_ids))
        )
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx, conn, query, cls,
                user_ids, lambda row: row['user_id'],
            )

    @classmethod
    async def get_groups_for_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_id: uuid.UUID,
    ) -> Sequence[Group]:
        j = sa.join(
            groups, association_groups_users,
            groups.c.id == association_groups_users.c.group_id,
        )
        query = (
            sa.select([groups])
            .select_from(j)
            .where(association_groups_users.c.user_id == user_id)
        )
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj async for row in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, row)) is not None
            ]


class GroupInput(graphene.InputObjectType):
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False, default=True)
    domain_name = graphene.String(required=True)
    total_resource_slots = graphene.JSONString(required=False)
    allowed_vfolder_hosts = graphene.List(lambda: graphene.String, required=False)
    integration_id = graphene.String(required=False)


class ModifyGroupInput(graphene.InputObjectType):
    name = graphene.String(required=False)
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    domain_name = graphene.String(required=False)
    total_resource_slots = graphene.JSONString(required=False)
    user_update_mode = graphene.String(required=False)
    user_uuids = graphene.List(lambda: graphene.String, required=False)
    allowed_vfolder_hosts = graphene.List(lambda: graphene.String, required=False)
    integration_id = graphene.String(required=False)


class CreateGroup(graphene.Mutation):

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        name = graphene.String(required=True)
        props = GroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    group = graphene.Field(lambda: Group, required=False)

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda name, props, **kwargs: (props.domain_name, None),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        name: str,
        props: GroupInput,
    ) -> CreateGroup:
        if _rx_slug.search(name) is None:
            raise ValueError('invalid name format. slug format required.')
        graph_ctx: GraphQueryContext = info.context
        data = {
            'name': name,
            'description': props.description,
            'is_active': props.is_active,
            'domain_name': props.domain_name,
            'total_resource_slots': ResourceSlot.from_user_input(
                props.total_resource_slots, None),
            'allowed_vfolder_hosts': props.allowed_vfolder_hosts,
            'integration_id': props.integration_id,
        }
        insert_query = (
            sa.insert(groups).values(data)
        )
        return await simple_db_mutate_returning_item(cls, graph_ctx, insert_query, item_cls=Group)


class ModifyGroup(graphene.Mutation):

    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)
        props = ModifyGroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    group = graphene.Field(lambda: Group, required=False)

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        gid: uuid.UUID,
        props: ModifyUserInput,
    ) -> ModifyGroup:
        graph_ctx: GraphQueryContext = info.context
        data: Dict[str, Any] = {}
        set_if_set(props, data, 'name')
        set_if_set(props, data, 'description')
        set_if_set(props, data, 'is_active')
        set_if_set(props, data, 'domain_name')
        set_if_set(props, data, 'total_resource_slots',
                   clean_func=lambda v: ResourceSlot.from_user_input(v, None))
        set_if_set(props, data, 'allowed_vfolder_hosts')
        set_if_set(props, data, 'integration_id')

        if 'name' in data and _rx_slug.search(data['name']) is None:
            raise ValueError('invalid name format. slug format required.')
        if props.user_update_mode not in (None, 'add', 'remove'):
            raise ValueError('invalid user_update_mode')
        if not props.user_uuids:
            props.user_update_mode = None
        if not data and props.user_update_mode is None:
            return cls(ok=False, msg='nothing to update', group=None)

        async def _do_mutate() -> ModifyGroup:
            async with graph_ctx.db.begin() as conn:
                # TODO: refactor user addition/removal in groups as separate mutations
                #       (to apply since 21.09)
                if props.user_update_mode == 'add':
                    values = [{'user_id': uuid, 'group_id': gid} for uuid in props.user_uuids]
                    await conn.execute(
                        sa.insert(association_groups_users).values(values),
                    )
                elif props.user_update_mode == 'remove':
                    await conn.execute(
                        sa.delete(association_groups_users)
                        .where(
                            (association_groups_users.c.user_id.in_(props.user_uuids)) &
                            (association_groups_users.c.group_id == gid),
                        ),
                    )
                if data:
                    result = await conn.execute(
                        sa.update(groups)
                        .values(data)
                        .where(groups.c.id == gid)
                        .returning(groups),
                    )
                    if result.rowcount > 0:
                        o = Group.from_row(graph_ctx, result.first())
                        return cls(ok=True, msg='success', group=o)
                    return cls(ok=False, msg='no such group', group=None)
                else:  # updated association_groups_users table
                    return cls(ok=True, msg='success', group=None)

        try:
            return await execute_with_retry(_do_mutate)
        except sa.exc.IntegrityError as e:
            return cls(ok=False, msg=f'integrity error: {e}', group=None)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            raise
        except Exception as e:
            return cls(ok=False, msg=f'unexpected error: {e}', group=None)


class DeleteGroup(graphene.Mutation):
    """
    Instead of deleting the group, just mark it as inactive.
    """
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> DeleteGroup:
        ctx: GraphQueryContext = info.context
        update_query = (
            sa.update(groups).values(
                is_active=False,
                integration_id=None,
            ).where(groups.c.id == gid)
        )
        return await simple_db_mutate(cls, ctx, update_query)


class PurgeGroup(graphene.Mutation):
    """
    Completely deletes a group from DB.

    Group's vfolders and their data will also be lost
    as well as the kernels run from the group.
    There is no migration of the ownership for group folders.
    """
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        gid = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    @privileged_mutation(
        UserRole.ADMIN,
        lambda gid, **kwargs: (None, gid),
    )
    async def mutate(cls, root, info: graphene.ResolveInfo, gid: uuid.UUID) -> PurgeGroup:
        graph_ctx: GraphQueryContext = info.context

        async def _pre_func(conn: SAConnection) -> None:
            if await cls.group_vfolder_mounted_to_active_kernels(conn, gid):
                raise RuntimeError(
                    "Some of virtual folders that belong to this group "
                    "are currently mounted to active sessions. "
                    "Terminate them first to proceed removal.",
                )
            if await cls.group_has_active_kernels(conn, gid):
                raise RuntimeError(
                    "Group has some active session. "
                    "Terminate them first to proceed removal.",
                )
            await cls.delete_vfolders(conn, gid, graph_ctx.storage_manager)
            await cls.delete_kernels(conn, gid)

        delete_query = sa.delete(groups).where(groups.c.id == gid)
        return await simple_db_mutate(cls, graph_ctx, delete_query, pre_func=_pre_func)

    @classmethod
    async def delete_vfolders(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """
        Delete group's all virtual folders as well as their physical data.

        :param conn: DB connection
        :param group_id: group's UUID to delete virtual folders

        :return: number of deleted rows
        """
        from . import vfolders
        query = (
            sa.select([vfolders.c.id, vfolders.c.host])
            .select_from(vfolders)
            .where(vfolders.c.group == group_id)
        )
        result = await db_conn.execute(query)
        target_vfs = result.fetchall()
        delete_query = (sa.delete(vfolders).where(vfolders.c.group == group_id))
        result = await db_conn.execute(delete_query)
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
            log.info('deleted {0} group\'s virtual folders ({1})', result.rowcount, group_id)
        return result.rowcount

    @classmethod
    async def delete_kernels(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
    ) -> int:
        """
        Delete all kernels run from the target groups.

        :param conn: DB connection
        :param group_id: group's UUID to delete kernels

        :return: number of deleted rows
        """
        from . import kernels
        query = (
            sa.delete(kernels)
            .where(kernels.c.group_id == group_id)
        )
        result = await db_conn.execute(query)
        if result.rowcount > 0:
            log.info('deleted {0} group\'s kernels ({1})', result.rowcount, group_id)
        return result.rowcount

    @classmethod
    async def group_vfolder_mounted_to_active_kernels(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
    ) -> bool:
        """
        Check if no active kernel is using the group's virtual folders.

        :param conn: DB connection
        :param group_id: group's ID

        :return: True if a virtual folder is mounted to active kernels.
        """
        from . import kernels, vfolders, AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES
        query = (
            sa.select([vfolders.c.id])
            .select_from(vfolders)
            .where(vfolders.c.group == group_id)
        )
        result = await db_conn.execute(query)
        rows = result.fetchall()
        group_vfolder_ids = [row['id'] for row in rows]
        query = (
            sa.select([kernels.c.mounts])
            .select_from(kernels)
            .where(
                (kernels.c.group_id == group_id) &
                (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
            )
        )
        async for row in (await db_conn.stream(query)):
            for _mount in row['mounts']:
                try:
                    vfolder_id = uuid.UUID(_mount[2])
                    if vfolder_id in group_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    @classmethod
    async def group_has_active_kernels(
        cls,
        db_conn: SAConnection,
        group_id: uuid.UUID,
    ) -> bool:
        """
        Check if the group does not have active kernels.

        :param conn: DB connection
        :param group_id: group's UUID

        :return: True if the group has some active kernels.
        """
        from . import kernels, AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES
        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where((kernels.c.group_id == group_id) &
                   (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)))
        )
        active_kernel_count = await db_conn.scalar(query)
        return True if active_kernel_count > 0 else False


class GroupDotfile(TypedDict):
    data: str
    path: str
    perm: str


async def query_group_dotfiles(
    db_conn: SAConnection,
    group_id: Union[GUID, uuid.UUID],
) -> tuple[list[GroupDotfile], int]:
    query = (
        sa.select([groups.c.dotfiles])
        .select_from(groups)
        .where(groups.c.id == group_id)
    )
    packed_dotfile = await db_conn.scalar(query)
    if packed_dotfile is None:
        return [], MAXIMUM_DOTFILE_SIZE
    rows = msgpack.unpackb(packed_dotfile)
    return rows, MAXIMUM_DOTFILE_SIZE - len(packed_dotfile)


async def query_group_domain(
    db_conn: SAConnection,
    group_id: Union[GUID, uuid.UUID],
) -> str:
    query = (
        sa.select([groups.c.domain_name])
        .select_from(groups)
        .where(groups.c.id == group_id)
    )
    domain = await db_conn.scalar(query)
    return domain


def verify_dotfile_name(dotfile: str) -> bool:
    if dotfile in RESERVED_DOTFILES:
        return False
    return True
