from __future__ import annotations

import enum
from typing import (
    Any,
    Iterable,
    List,
    Mapping,
    Sequence,
)
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.types import SessionTypes

from ..defs import DEFAULT_ROLE
from ..exceptions import InvalidArgument
from .base import metadata, GUID, IDColumn, EnumType
from .user import UserRole
from .vfolder import verify_vfolder_name

__all__: Sequence[str] = (
    'TemplateType', 'session_templates', 'query_accessible_session_templates',
)


class TemplateType(str, enum.Enum):
    TASK = 'task'
    CLUSTER = 'cluster'


session_templates = sa.Table(
    'session_templates', metadata,
    IDColumn('id'),
    sa.Column('created_at', sa.DateTime(timezone=True),
               server_default=sa.func.now(), index=True),
    sa.Column('is_active', sa.Boolean, default=True),

    sa.Column('domain_name', sa.String(length=64), sa.ForeignKey('domains.name'), nullable=False),
    sa.Column('group_id', GUID, sa.ForeignKey('groups.id'), nullable=True),
    sa.Column('user_uuid', GUID, sa.ForeignKey('users.uuid'), index=True, nullable=False),
    sa.Column('type', EnumType(TemplateType), nullable=False, server_default='TASK', index=True),

    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('template', pgsql.JSONB(), nullable=False),
)


task_template_v1 = t.Dict({
    tx.AliasedKey(['api_version', 'apiVersion']): t.String,
    t.Key('kind'): t.Enum('taskTemplate', 'task_template'),
    t.Key('metadata'): t.Dict({
        t.Key('name'): t.String,
        t.Key('tag', default=None): t.Null | t.String,
    }),
    t.Key('spec'): t.Dict({
        tx.AliasedKey(['type', 'session_type', 'sessionType'],
                      default='interactive') >> 'session_type': tx.Enum(SessionTypes),
        t.Key('kernel'): t.Dict({
            t.Key('image'): t.String,
            t.Key('architecture', default='x86_64'): t.Null | t.String,
            t.Key('environ', default={}): t.Null | t.Mapping(t.String, t.String),
            t.Key('run', default=None): t.Null | t.Dict({
                t.Key('bootstrap', default=None): t.Null | t.String,
                tx.AliasedKey(['startup', 'startup_command', 'startupCommand'],
                              default=None) >> 'startup_command': t.Null | t.String,
            }),
            t.Key('git', default=None): t.Null | t.Dict({
                t.Key('repository'): t.String,
                t.Key('commit', default=None): t.Null | t.String,
                t.Key('branch', default=None): t.Null | t.String,
                t.Key('credential', default=None): t.Null | t.Dict({
                    t.Key('username'): t.String,
                    t.Key('password'): t.String,
                }),
                tx.AliasedKey(['destination_dir', 'destinationDir'],
                              default=None) >> 'dest_dir': t.Null | t.String,
            }),
        }),
        t.Key('scaling_group', default=None): t.Null | t.String,
        t.Key('mounts', default={}): t.Null | t.Mapping(t.String, t.Any),
        t.Key('resources', default=None): t.Null | t.Mapping(t.String, t.Any),
        tx.AliasedKey(['agent_list', 'agentList'],
                      default=None) >> 'agent_list': t.Null | t.List(t.String),
    }),
}).allow_extra('*')


def check_task_template(raw_data: Mapping[str, Any]) -> Mapping[str, Any]:
    data = task_template_v1.check(raw_data)
    if mounts := data['spec'].get('mounts'):
        for p in mounts.values():
            if p is None:
                continue
            if p.startswith("/home/work/"):
                p = p.replace("/home/work/", "")
            if not verify_vfolder_name(p):
                raise InvalidArgument(f'Path {p} is reserved for internal operations.')
    return data


cluster_template_v1 = t.Dict({
    tx.AliasedKey(['api_version', 'apiVersion']): t.String,
    t.Key('kind'): t.Enum('clusterTemplate', 'cluster_template'),
    t.Key('mode'): t.Enum('single-node', 'multi-node'),
    t.Key('metadata'): t.Dict({
        t.Key('name'): t.String,
    }),
    t.Key('spec'): t.Dict({
        t.Key('environ', default={}): t.Null | t.Mapping(t.String, t.String),
        t.Key('mounts', default={}): t.Null | t.Mapping(t.String, t.Any),
        t.Key('nodes'): t.List(t.Dict({
            t.Key('role'): t.String,
            tx.AliasedKey(['session_template', 'sessionTemplate']): tx.UUID,
            t.Key('replicas', default=1): t.Int,
        })),
    }),
}).allow_extra('*')


def check_cluster_template(raw_data: Mapping[str, Any]) -> Mapping[str, Any]:
    data = cluster_template_v1.check(raw_data)
    defined_roles: List[str] = []
    for node in data['spec']['nodes']:
        node['session_template'] = str(node['session_template'])
        if node['role'] in defined_roles:
            raise InvalidArgument("Each role can only be defined once")
        if node['role'] == DEFAULT_ROLE and node['replicas'] != 1:
            raise InvalidArgument(
                f"One and only one {DEFAULT_ROLE} node must be created per cluster",
            )
        defined_roles.append(node['role'])
    if DEFAULT_ROLE not in defined_roles:
        raise InvalidArgument(
            f"One and only one {DEFAULT_ROLE} node must be created per cluster",
        )
    return data


async def query_accessible_session_templates(
    conn: SAConnection,
    user_uuid: uuid.UUID,
    template_type: TemplateType,
    *,
    user_role: UserRole = None,
    domain_name: str = None,
    allowed_types: Iterable[str] = ['user'],
    extra_conds=None,
) -> List[Mapping[str, Any]]:
    from ai.backend.manager.models import groups, users, association_groups_users as agus
    entries: List[Mapping[str, Any]] = []
    if 'user' in allowed_types:
        # Query user templates
        j = (session_templates.join(users, session_templates.c.user_uuid == users.c.uuid))
        query = (
            sa.select([
                session_templates.c.name,
                session_templates.c.id,
                session_templates.c.created_at,
                session_templates.c.user_uuid,
                session_templates.c.group_id,
                users.c.email,
            ])
            .select_from(j)
            .where(
                (session_templates.c.user_uuid == user_uuid) &
                session_templates.c.is_active &
                (session_templates.c.type == template_type),
            )
        )
        if extra_conds is not None:
            query = query.where(extra_conds)
        result = await conn.execute(query)
        for row in result:
            entries.append({
                'name': row.name,
                'id': row.id,
                'created_at': row.created_at,
                'is_owner': True,
                'user': str(row.user_uuid) if row.user_uuid else None,
                'group': str(row.group_id) if row.group_id else None,
                'user_email': row.email,
                'group_name': None,
            })
    if 'group' in allowed_types:
        # Query group session_templates
        if user_role == UserRole.ADMIN or user_role == 'admin':
            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == domain_name)
            )
            result = await conn.execute(query)
            grps = result.fetchall()
            group_ids = [g.id for g in grps]
        else:
            j = sa.join(agus, users, agus.c.user_id == users.c.uuid)
            query = (
                sa.select([agus.c.group_id])
                .select_from(j)
                .where(agus.c.user_id == user_uuid)
            )
            result = await conn.execute(query)
            grps = result.fetchall()
            group_ids = [g.group_id for g in grps]
        j = (session_templates.join(groups, session_templates.c.group_id == groups.c.id))
        query = (
            sa.select([
                session_templates.c.name,
                session_templates.c.id,
                session_templates.c.created_at,
                session_templates.c.user_uuid,
                session_templates.c.group_id,
                groups.c.name,
            ], use_labels=True)
            .select_from(j)
            .where(
                session_templates.c.group_id.in_(group_ids) &
                session_templates.c.is_active &
                (session_templates.c.type == template_type),
            )
        )
        if extra_conds is not None:
            query = query.where(extra_conds)
        if 'user' in allowed_types:
            query = query.where(session_templates.c.user_uuid != user_uuid)
        result = await conn.execute(query)
        is_owner = (user_role == UserRole.ADMIN or user_role == 'admin')
        for row in result:
            entries.append({
                'name': row.session_templates_name,
                'id': row.session_templates_id,
                'created_at': row.session_templates_created_at,
                'is_owner': is_owner,
                'user': (str(row.session_templates_user_uuid) if row.session_templates_user_uuid
                         else None),
                'group': str(row.session_templates_group_id) if row.session_templates_group_id else None,
                'user_email': None,
                'group_name': row.groups_name,
            })
    return entries
