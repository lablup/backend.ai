import logging
from typing import (
    Any,
    Iterable,
    TYPE_CHECKING,
    Tuple,
)

from aiohttp import web
import aiohttp
import aiohttp_cors
import aiotools
from dataclasses import dataclass, field
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.common.logging import BraceStyleAdapter

from ai.backend.manager.api.exceptions import ObjectNotFound

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from ..models import (
    query_allowed_sgroups,
)
from .auth import auth_required
from .manager import (
    READ_ALLOWED,
    server_status_required)
from .types import CORSOptions, WebMiddleware
from .utils import check_api_params

if TYPE_CHECKING:
    from .context import RootContext

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass(unsafe_hash=True)
class WSProxyVersionQueryParams:
    db_ctx: ExtendedAsyncSAEngine = field(hash=False)


@aiotools.lru_cache(expire_after=30)  # expire after 30 seconds
async def query_wsproxy_version(
    wsproxy_addr: str,
) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(wsproxy_addr + '/status') as resp:
            version_json = await resp.json()
            return version_json['api_version']


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(
    t.Dict({
        tx.AliasedKey(['group', 'group_id', 'group_name']): tx.UUID | t.String,
    }),
)
async def list_available_sgroups(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    access_key = request['keypair']['access_key']
    domain_name = request['user']['domain_name']
    group_id_or_name = params['group']
    log.info('SGROUPS.LIST(ak:{}, g:{}, d:{})', access_key, group_id_or_name, domain_name)
    async with root_ctx.db.begin() as conn:
        sgroups = await query_allowed_sgroups(
            conn, domain_name, group_id_or_name, access_key)
        return web.json_response({
            'scaling_groups': [
                {'name': sgroup['name']}
                for sgroup in sgroups
            ],
        }, status=200)


@auth_required
@server_status_required(READ_ALLOWED)
@check_api_params(t.Dict({
        tx.AliasedKey(['group', 'group_id', 'group_name'], default=None): t.Null | tx.UUID | t.String,
}))
async def get_wsproxy_version(request: web.Request, params: Any) -> web.Response:
    root_ctx: RootContext = request.app['_root.context']
    scaling_group_name = request.match_info['scaling_group']
    access_key = request['keypair']['access_key']
    domain_name = request['user']['domain_name']
    group_id_or_name = params['group']
    log.info('SGROUPS.LIST(ak:{}, g:{}, d:{})', access_key, group_id_or_name, domain_name)
    async with root_ctx.db.begin_readonly() as conn:
        sgroups = await query_allowed_sgroups(
            conn, domain_name, group_id_or_name or '', access_key)
        for sgroup in sgroups:
            if sgroup['name'] == scaling_group_name:
                wsproxy_addr = sgroup['wsproxy_addr']
                if not wsproxy_addr:
                    wsproxy_version = 'v1'
                else:
                    wsproxy_version = await query_wsproxy_version(wsproxy_addr)
                return web.json_response({
                    'wsproxy_version': wsproxy_version,
                })
        else:
            raise ObjectNotFound(object_name='scaling group')


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(default_cors_options: CORSOptions) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app['prefix'] = 'scaling-groups'
    app['api_versions'] = (2, 3, 4)
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    root_resource = cors.add(app.router.add_resource(r''))
    cors.add(root_resource.add_route('GET',  list_available_sgroups))
    cors.add(app.router.add_route('GET',  '/{scaling_group}/wsproxy-version', get_wsproxy_version))
    return app, []
