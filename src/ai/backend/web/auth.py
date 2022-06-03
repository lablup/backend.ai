import copy
import json

from aiohttp import web
from aiohttp_session import get_session

from ai.backend.client.session import AsyncSession as APISession
from ai.backend.client.config import APIConfig

from . import user_agent


async def get_api_session(
    request: web.Request,
    api_endpoint: str = None,
) -> APISession:
    config = request.app['config']
    if api_endpoint is not None:
        config = copy.deepcopy(config)
        config['api']['endpoint'] = api_endpoint
    session = await get_session(request)
    if not session.get('authenticated', False):
        raise web.HTTPUnauthorized(text=json.dumps({
            'type': 'https://api.backend.ai/probs/auth-failed',
            'title': 'Unauthorized access',
        }), content_type='application/problem+json')
    if 'token' not in session:
        raise web.HTTPUnauthorized(text=json.dumps({
            'type': 'https://api.backend.ai/probs/auth-failed',
            'title': 'Unauthorized access',
        }), content_type='application/problem+json')
    token = session['token']
    if token['type'] != 'keypair':
        raise web.HTTPBadRequest(text=json.dumps({
            'type': 'https://api.backend.ai/probs/invalid-auth-params',
            'title': 'Incompatible auth token type.',
        }), content_type='application/problem+json')
    ak, sk = token['access_key'], token['secret_key']
    config = APIConfig(
        domain=config['api']['domain'],
        endpoint=config['api']['endpoint'],
        access_key=ak,
        secret_key=sk,
        user_agent=user_agent,
        skip_sslcert_validation=not config['api'].get('ssl-verify', True),
    )
    return APISession(config=config, proxy_mode=True)


async def get_anonymous_session(
    request: web.Request,
    api_endpoint: str = None,
) -> APISession:
    config = request.app['config']
    if api_endpoint is not None:
        config = copy.deepcopy(config)
        config['api']['endpoint'] = api_endpoint
    config = APIConfig(
        domain=config['api']['domain'],
        endpoint=config['api']['endpoint'],
        access_key='',
        secret_key='',
        user_agent=user_agent,
        skip_sslcert_validation=not config['api'].get('ssl-verify', True),
    )
    return APISession(config=config, proxy_mode=True)
