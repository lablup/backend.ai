import json
import datetime
import logging
from typing import (
    Any,
    List,
    Dict,
    Mapping,
    TYPE_CHECKING,
    Tuple,
)
import uuid

from aiohttp import web
import aiohttp_cors
import sqlalchemy as sa
import trafaret as t
import yaml

from ai.backend.common import validators as tx
from ai.backend.common.logging import BraceStyleAdapter

from ..models import (
    groups, session_templates, users, TemplateType,
)
from ..models.session_template import check_task_template

from .auth import auth_required
from .exceptions import InvalidAPIParameters, TaskTemplateNotFound
from .manager import READ_ALLOWED, server_status_required
from .types import CORSOptions, Iterable, WebMiddleware
from .utils import check_api_params, get_access_key_scopes
from .session import _query_userinfo

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@server_status_required(READ_ALLOWED)
@auth_required
@check_api_params(t.Dict(
    {
        tx.AliasedKey(['group', 'groupName', 'group_name'], default='default'): t.String,
        tx.AliasedKey(['domain', 'domainName', 'domain_name'], default='default'): t.String,
        t.Key('owner_access_key', default=None): t.Null | t.String,
        t.Key('payload'): t.String,
    },
))
async def create(request: web.Request, params: Any) -> web.Response:
    if params['domain'] is None:
        params['domain'] = request['user']['domain_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        'SESSION_TEMPLATE.CREATE (ak:{0}/{1})',
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else '*',
    )
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin() as conn:
        user_uuid, group_id, _ = await _query_userinfo(request, params, conn)
        log.debug('Params: {0}', params)
        try:
            body = json.loads(params['payload'])
        except json.JSONDecodeError:
            try:
                body = yaml.safe_load(params['payload'])
            except (yaml.YAMLError, yaml.MarkedYAMLError):
                raise InvalidAPIParameters('Malformed payload')
        for st in body['session_templates']:
            template_data = check_task_template(st['template'])
            template_id = uuid.uuid4().hex
            resp = {
                'id': template_id,
                'user': user_uuid.hex,
            }
            name = st['name'] if 'name' in st else template_data['metadata']['name']
            if 'group_id' in st:
                group_id = st['group_id']
            if 'user_uuid' in st:
                user_uuid = st['user_uuid']
            query = session_templates.insert().values({
                'id': template_id,
                'created_at': datetime.datetime.now(),
                'domain_name': params['domain'],
                'group_id': group_id,
                'user_uuid': user_uuid,
                'name': name,
                'template': template_data,
                'type': TemplateType.TASK,
            })
            result = await conn.execute(query)
            assert result.rowcount == 1
    return web.json_response(resp)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key('all', default=False): t.ToBool,
        tx.AliasedKey(['group_id', 'groupId'], default=None): tx.UUID | t.String | t.Null,
    }),
)
async def list_template(request: web.Request, params: Any) -> web.Response:
    resp = []
    access_key = request['keypair']['access_key']
    domain_name = request['user']['domain_name']
    user_uuid = request['user']['uuid']
    log.info('SESSION_TEMPLATE.LIST (ak:{})', access_key)
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin() as conn:
        entries: List[Mapping[str, Any]]
        j = (
            session_templates
            .join(users, session_templates.c.user_uuid == users.c.uuid, isouter=True)
            .join(groups, session_templates.c.group_id == groups.c.id, isouter=True)
        )
        query = (
            sa.select([session_templates, users.c.email, groups.c.name], use_labels=True)
            .select_from(j)
            .where(
                (session_templates.c.is_active) &
                (session_templates.c.type == TemplateType.TASK),
            )
        )
        result = await conn.execute(query)
        entries = []
        for row in result.fetchall():
            is_owner = True if row.session_templates_user_uuid == user_uuid else False
            entries.append({
                'name': row.session_templates_name,
                'id': row.session_templates_id,
                'created_at': row.session_templates_created_at,
                'is_owner': is_owner,
                'user': (str(row.session_templates_user_uuid)
                            if row.session_templates_user_uuid else None),
                'group': (str(row.session_templates_group_id)
                            if row.session_templates_group_id else None),
                'user_email': row.users_email,
                'group_name': row.groups_name,
                'domain_name': domain_name,
                'type': row.session_templates_type,
                'template': row.session_templates_template,
            })
        for entry in entries:
            resp.append({
                'name': entry['name'],
                'id': entry['id'].hex,
                'created_at': str(entry['created_at']),
                'is_owner': entry['is_owner'],
                'user': str(entry['user']),
                'group': str(entry['group']),
                'user_email': entry['user_email'],
                'group_name': entry['group_name'],
                'domain_name': domain_name,
                'type': entry['type'],
                'template': entry['template'],
            })
        return web.json_response(resp)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key('format', default='json'): t.Null | t.Enum('yaml', 'json'),
        t.Key('owner_access_key', default=None): t.Null | t.String,
    }),
)
async def get(request: web.Request, params: Any) -> web.Response:
    if params['format'] not in ['yaml', 'json']:
        raise InvalidAPIParameters('format should be "yaml" or "json"')
    resp: Dict[str, Any] = {}
    domain_name = request['user']['domain_name']
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        'SESSION_TEMPLATE.GET (ak:{0}/{1})',
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else '*',
    )
    template_id = request.match_info['template_id']
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([
                session_templates.c.template,
                session_templates.c.name,
                session_templates.c.user_uuid,
                session_templates.c.group_id,
            ])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == template_id) &
                (session_templates.c.is_active) &
                (session_templates.c.type == TemplateType.TASK),
            )
        )
        result = await conn.execute(query)
        for row in result.fetchall():
            resp.update({
                'template': row.template,
                'name': row.name,
                'user_uuid': str(row.user_uuid),
                'group_id': str(row.group_id),
                'domain_name': domain_name,
            })
        if isinstance(resp, str):
            resp = json.loads(resp)
        else:
            resp = json.loads(json.dumps(resp))
        return web.json_response(resp)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        tx.AliasedKey(['group', 'groupName', 'group_name'], default='default'): t.String,
        tx.AliasedKey(['domain', 'domainName', 'domain_name'], default='default'): t.String,
        t.Key('payload'): t.String,
        t.Key('owner_access_key', default=None): t.Null | t.String,
    }),
)
async def put(request: web.Request, params: Any) -> web.Response:
    if params['domain'] is None:
        params['domain'] = request['user']['domain_name']
    template_id = request.match_info['template_id']

    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        'SESSION_TEMPLATE.PUT (ak:{0}/{1})',
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else '*',
    )
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin() as conn:
        user_uuid, group_id, _ = await _query_userinfo(request, params, conn)
        query = (
            sa.select([session_templates.c.id])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == template_id) &
                (session_templates.c.is_active) &
                (session_templates.c.type == TemplateType.TASK),
            )
        )
        result = await conn.scalar(query)
        if not result:
            raise TaskTemplateNotFound
        try:
            body = json.loads(params['payload'])
        except json.JSONDecodeError:
            body = yaml.safe_load(params['payload'])
        except (yaml.YAMLError, yaml.MarkedYAMLError):
            raise InvalidAPIParameters('Malformed payload')
        for st in body['session_templates']:
            template_data = check_task_template(st['template'])
            name = st['name'] if 'name' in st else template_data['metadata']['name']
            if 'group_id' in st:
                group_id = st['group_id']
            if 'user_uuid' in st:
                user_uuid = st['user_uuid']
            query = (
                sa.update(session_templates)
                .values({
                    'group_id': group_id,
                    'user_uuid': user_uuid,
                    'name': name,
                    'template': template_data,
                })
                .where((session_templates.c.id == template_id))
            )
            result = await conn.execute(query)
            assert result.rowcount == 1
        return web.json_response({'success': True})


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        t.Key('owner_access_key', default=None): t.Null | t.String,
    }),
)
async def delete(request: web.Request, params: Any) -> web.Response:
    template_id = request.match_info['template_id']
    requester_access_key, owner_access_key = await get_access_key_scopes(request, params)
    log.info(
        'SESSION_TEMPLATE.DELETE (ak:{0}/{1})',
        requester_access_key,
        owner_access_key if owner_access_key != requester_access_key else '*',
    )
    root_ctx: RootContext = request.app['_root.context']
    async with root_ctx.db.begin() as conn:
        query = (
            sa.select([session_templates.c.id])
            .select_from(session_templates)
            .where(
                (session_templates.c.id == template_id) &
                (session_templates.c.is_active) &
                (session_templates.c.type == TemplateType.TASK),
            )
        )
        result = await conn.scalar(query)
        if not result:
            raise TaskTemplateNotFound
        query = (
            sa.update(session_templates)
            .values(is_active=False)
            .where((session_templates.c.id == template_id))
        )
        result = await conn.execute(query)
        assert result.rowcount == 1

        return web.json_response({'success': True})


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app['api_versions'] = (4, 5)
    app['prefix'] = 'template/session'
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    cors.add(app.router.add_route('POST', '', create))
    cors.add(app.router.add_route('GET', '', list_template))
    template_resource = cors.add(app.router.add_resource(r'/{template_id}'))
    cors.add(template_resource.add_route('GET', get))
    cors.add(template_resource.add_route('PUT', put))
    cors.add(template_resource.add_route('DELETE', delete))

    return app, []
