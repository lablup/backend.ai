import asyncio
from functools import partial
import logging
import logging.config
import json
import os
from pathlib import Path
import pkg_resources
from pprint import pprint
import re
import socket
import ssl
import sys
import time
from typing import (
    Any,
    AsyncIterator,
    MutableMapping,
    Tuple,
)

from aiohttp import web
import aiohttp_cors
from aiohttp_session import get_session, setup as setup_session
from aiohttp_session.redis_storage import RedisStorage
import aiotools
import aioredis
import click
import jinja2
from setproctitle import setproctitle
import toml
import uvloop
import yarl

from ai.backend.client.config import APIConfig
from ai.backend.client.exceptions import BackendClientError, BackendAPIError
from ai.backend.client.session import AsyncSession as APISession

from . import __version__, user_agent
from .logging import BraceStyleAdapter
from .proxy import web_handler, websocket_handler, web_plugin_handler

log = BraceStyleAdapter(logging.getLogger('ai.backend.web.server'))
static_path = Path(pkg_resources.resource_filename('ai.backend.web', 'static')).resolve()
assert static_path.is_dir()


console_config_ini_template = jinja2.Template('''[general]
apiEndpoint = {{endpoint_url}}
apiEndpointText = {{endpoint_text}}
{% if default_environment %}
defaultSessionEnvironment = "{{default_environment}}"
{% endif %}
siteDescription = {{site_description}}
connectionMode = "SESSION"

[wsproxy]
proxyURL = {{proxy_url}}/
proxyBaseURL =
proxyListenIP =
''')

console_config_toml_template = jinja2.Template('''[general]
apiEndpoint = "{{endpoint_url}}"
apiEndpointText = "{{endpoint_text}}"
{% if default_environment %}
defaultSessionEnvironment = "{{default_environment}}"
{% endif %}
{% if default_import_environment %}
defaultImportEnvironment = "{{default_import_environment}}"
{% endif %}
siteDescription = "{{site_description}}"
connectionMode = "SESSION"
signupSupport = {{signup_support}}
allowChangeSigninMode = {{allow_change_signin_mode}}
allowAnonymousChangePassword = {{allow_anonymous_change_password}}
allowProjectResourceMonitor = {{allow_project_resource_monitor}}
allowManualImageNameForSession = {{allow_manual_image_name_for_session}}
allowSignupWithoutConfirmation = {{allow_signup_without_confirmation}}
autoLogout = {{auto_logout}}
debug = {{webui_debug}}
maskUserInfo = {{mask_user_info}}

[resources]
openPortToPublic = {{open_port_to_public}}
maxCPUCoresPerContainer = {{max_cpu_cores_per_container}}
maxMemoryPerContainer = {{max_memory_per_container}}
maxCUDADevicesPerContainer = {{max_cuda_devices_per_container}}
maxCUDASharesPerContainer = {{max_cuda_shares_per_container}}
maxShmPerContainer = {{max_shm_per_container}}
maxFileUploadSize = {{max_file_upload_size}}

[environments]
{% if environment_allowlist %}
allowlist = "{{environment_allowlist}}"
{% endif %}

[menu]
{% if menu_blocklist %}
blocklist = "{{menu_blocklist}}"
{% endif %}

{% if console_menu_plugins %}
[plugin]
page = "{{console_menu_plugins}}"

{% endif %}
[wsproxy]
proxyURL = "{{proxy_url}}/"
#proxyBaseURL =
#proxyListenIP =

[license]
edition = "{{license_edition}}"
validSince = "{{license_valid_since}}"
validUntil = "{{license_valid_until}}"
''')


async def static_handler(request: web.Request) -> web.StreamResponse:
    request_path = request.match_info['path']
    file_path = (static_path / request_path).resolve()
    try:
        file_path.relative_to(static_path)
    except (ValueError, FileNotFoundError):
        return web.HTTPNotFound(text=json.dumps({
            'type': 'https://api.backend.ai/probs/generic-not-found',
            'title': 'Not Found',
        }), content_type='application/problem+json')
    if file_path.is_file():
        return header_handler(web.FileResponse(file_path), request_path)
    return web.HTTPNotFound(text=json.dumps({
        'type': 'https://api.backend.ai/probs/generic-not-found',
        'title': 'Not Found',
    }), content_type='application/problem+json')


async def console_handler(request: web.Request) -> web.StreamResponse:
    request_path = request.match_info['path']
    file_path = (static_path / request_path).resolve()
    config = request.app['config']
    scheme = config['service'].get('force-endpoint-protocol')
    if scheme is None:
        scheme = request.scheme

    if request_path == 'config.ini':
        config_content = console_config_ini_template.render(**{
            'endpoint_url': f'{scheme}://{request.host}',  # must be absolute
            'endpoint_text': config['api']['text'],
            'site_description': config['ui']['brand'],
            'default_environment': config['ui'].get('default_environment'),
            'proxy_url': config['service']['wsproxy']['url'],
        })
        return web.Response(text=config_content)

    if request_path == 'config.toml':
        if 'license' in config:
            license_edition = config['license'].get('edition', 'Open Source')
            license_valid_since = config['license'].get('valid_since', '')
            license_valid_until = config['license'].get('valid_until', '')
        else:
            license_edition = 'Open Source'
            license_valid_since = ''
            license_valid_until = ''
        if 'resources' in config:
            open_port_to_public = 'true' if config['resources'].get('open_port_to_public') else 'false'
            max_cpu_cores_per_container = config['resources'].get('max_cpu_cores_per_container', 64)
            max_memory_per_container = config['resources'].get('max_memory_per_container', 64)
            max_cuda_devices_per_container = config['resources'].get(
                    'max_cuda_devices_per_container', 16)
            max_cuda_shares_per_container = config['resources'].get(
                    'max_cuda_shares_per_container', 16)
            max_shm_per_container = config['resources'].get('max_shm_per_container', 2)
            max_file_upload_size = config['resources'].get('max_file_upload_size', 4294967296)
        else:
            open_port_to_public = 'false'
            max_cpu_cores_per_container = 64
            max_memory_per_container = 64
            max_cuda_devices_per_container = 16
            max_cuda_shares_per_container = 16
            max_shm_per_container = 2
            max_file_upload_size = 4294967296
        if 'plugin' in config:
            console_menu_plugins = config['plugin'].get('page', '')
        else:
            console_menu_plugins = False
        config_content = console_config_toml_template.render(**{
            'endpoint_url': f'{scheme}://{request.host}',  # must be absolute
            'endpoint_text': config['api']['text'],
            'site_description': config['ui']['brand'],
            'default_environment': config['ui'].get('default_environment'),
            'default_import_environment': config['ui'].get('default_import_environment'),
            'proxy_url': config['service']['wsproxy']['url'],
            'signup_support': 'true' if config['service']['enable_signup'] else 'false',
            'allow_change_signin_mode':
                'true' if config['service'].get('allow_change_signin_mode') else 'false',
            'allow_anonymous_change_password':
                'true' if config['service'].get('allow_anonymous_change_password') else 'false',
            'allow_project_resource_monitor':
                'true' if config['service']['allow_project_resource_monitor'] else 'false',
            'allow_manual_image_name_for_session':
                'true' if config['service'].get('allow_manual_image_name_for_session') else 'false',
            'allow_signup_without_confirmation':
                'true' if config['service'].get('allow_signup_without_confirmation') else 'false',
            'webui_debug': 'true' if config['service'].get('webui_debug') else 'false',
            'auto_logout':
                'true' if config['session'].get('auto_logout') else 'false',
            'mask_user_info':
                'true' if config['service'].get('mask_user_info') else 'false',
            'open_port_to_public': open_port_to_public,
            'max_cpu_cores_per_container': max_cpu_cores_per_container,
            'max_memory_per_container': max_memory_per_container,
            'max_cuda_devices_per_container': max_cuda_devices_per_container,
            'max_cuda_shares_per_container': max_cuda_shares_per_container,
            'max_shm_per_container': max_shm_per_container,
            'max_file_upload_size': max_file_upload_size,
            'environment_allowlist': config['environments'].get('allowlist', ''),
            'menu_blocklist': config['ui'].get('menu_blocklist', ''),
            'console_menu_plugins': console_menu_plugins,
            'license_edition': license_edition,
            'license_valid_since': license_valid_since,
            'license_valid_until': license_valid_until,
        })
        return web.Response(text=config_content)
    # SECURITY: only allow reading files under static_path
    try:
        file_path.relative_to(static_path)
    except (ValueError, FileNotFoundError):
        return web.HTTPNotFound(text=json.dumps({
            'type': 'https://api.backend.ai/probs/generic-not-found',
            'title': 'Not Found',
        }), content_type='application/problem+json')
    if file_path.is_file():
        return header_handler(web.FileResponse(file_path), request_path)

    return header_handler(web.FileResponse(static_path / 'index.html'), 'index.html')


cache_patterns = {
    r'\.(?:manifest|appcache|html?|xml|json|ini|toml)$': {
        'Cache-Control': 'no-store'
    },
    r'(?:backend.ai-webui.js)$': {
        'Cache-Control': 'no-store'
    },
    r'\.(?:jpg|jpeg|gif|png|ico|cur|gz|svg|svgz|mp4|ogg|ogv|webm|htc|woff|woff2)$': {
        'Cache-Control': 'max-age=259200, public',
    },
    r'\.(?:css|js)$': {
        'Cache-Control': 'max-age=86400, public, must-revalidate, proxy-revalidate',
    },
    r'\.(?:py|log?|txt)$': {
        'Cache-Control': 'no-store'
    },
}
_cache_patterns = {re.compile(k): v for k, v in cache_patterns.items()}


def header_handler(response: web.StreamResponse, path: str) -> web.StreamResponse:
    for regex, headers in _cache_patterns.items():
        mo = regex.search(path)
        if mo is not None:
            response.headers.update(headers)
            break
    return response


async def login_check_handler(request: web.Request) -> web.Response:
    session = await get_session(request)
    authenticated = bool(session.get('authenticated', False))
    public_data = None
    if authenticated:
        stored_token = session['token']
        public_data = {
            'access_key': stored_token['access_key'],
            'role': stored_token['role'],
            'status': stored_token.get('status'),
        }
    return web.json_response({
        'authenticated': authenticated,
        'data': public_data,
        'session_id': session.identity,  # temporary wsproxy interop patch
    })


async def login_handler(request: web.Request) -> web.Response:
    config = request.app['config']
    session = await get_session(request)
    if session.get('authenticated', False):
        return web.HTTPBadRequest(text=json.dumps({
            'type': 'https://api.backend.ai/probs/generic-bad-request',
            'title': 'You have already logged in.',
        }), content_type='application/problem+json')
    creds = await request.json()
    if 'username' not in creds or not creds['username']:
        return web.HTTPBadRequest(text=json.dumps({
            'type': 'https://api.backend.ai/probs/invalid-api-params',
            'title': 'You must provide the username field.',
        }), content_type='application/problem+json')
    if 'password' not in creds or not creds['password']:
        return web.HTTPBadRequest(text=json.dumps({
            'type': 'https://api.backend.ai/probs/invalid-api-params',
            'title': 'You must provide the password field.',
        }), content_type='application/problem+json')
    result: MutableMapping[str, Any] = {
        'authenticated': False,
        'data': None,
    }
    try:
        async def _get_login_history():
            login_history = await request.app['redis'].get(
                f'login_history_{creds["username"]}',
            )
            if not login_history:
                login_history = {
                    'last_login_attempt': 0,
                    'login_fail_count': 0,
                }
            else:
                login_history = json.loads(login_history)
            if login_history['last_login_attempt'] < 0:
                login_history['last_login_attempt'] = 0
            if login_history['login_fail_count'] < 0:
                login_history['login_fail_count'] = 0
            return login_history

        async def _set_login_history(last_login_attempt, login_fail_count):
            """
            Set login history per email (not in browser session).
            """
            key = f'login_history_{creds["username"]}'
            value = json.dumps({
                'last_login_attempt': last_login_attempt,
                'login_fail_count': login_fail_count,
            })
            await request.app['redis'].set(key, value)

        # Block login if there are too many consecutive failed login attempts.
        BLOCK_TIME = config['session'].get('login_block_time', 1200)
        ALLOWED_FAIL_COUNT = config['session'].get('login_allowed_fail_count', 10)
        login_time = time.time()
        login_history = await _get_login_history()
        last_login_attempt = login_history.get('last_login_attempt', 0)
        login_fail_count = login_history.get('login_fail_count', 0)
        if login_time - last_login_attempt > BLOCK_TIME:
            # If last attempt is far past, allow login again.
            login_fail_count = 0
        last_login_attempt = login_time
        if login_fail_count >= ALLOWED_FAIL_COUNT:
            log.info('Too many consecutive login attempts for {}: {}',
                     creds['username'], login_fail_count)
            await _set_login_history(last_login_attempt, login_fail_count)
            return web.HTTPTooManyRequests(text=json.dumps({
                'type': 'https://api.backend.ai/probs/too-many-requests',
                'title': 'Too many failed login attempts',
            }), content_type='application/problem+json')

        anon_api_config = APIConfig(
            domain=config['api']['domain'],
            endpoint=config['api']['endpoint'],
            access_key='', secret_key='',  # anonymous session
            user_agent=user_agent,
            skip_sslcert_validation=not config['api'].get('ssl-verify', True),
        )
        assert anon_api_config.is_anonymous
        async with APISession(config=anon_api_config) as api_session:
            token = await api_session.User.authorize(creds['username'], creds['password'])
            stored_token = {
                'type': 'keypair',
                'access_key': token.content['access_key'],
                'secret_key': token.content['secret_key'],
                'role': token.content['role'],
                'status': token.content.get('status'),
            }
            public_return = {
                'access_key': token.content['access_key'],
                'role': token.content['role'],
                'status': token.content.get('status'),
            }
            session['authenticated'] = True
            session['token'] = stored_token  # store full token
            result['authenticated'] = True
            result['data'] = public_return  # store public info from token
            login_fail_count = 0
            await _set_login_history(last_login_attempt, login_fail_count)
    except BackendClientError as e:
        # This is error, not failed login, so we should not update login history.
        return web.HTTPBadGateway(text=json.dumps({
            'type': 'https://api.backend.ai/probs/bad-gateway',
            'title': "The proxy target server is inaccessible.",
            'details': str(e),
        }), content_type='application/problem+json')
    except BackendAPIError as e:
        log.info('Authorization failed for {}: {}', creds['username'], e)
        result['authenticated'] = False
        result['data'] = {
            'type': e.data.get('type'),
            'title': e.data.get('title'),
            'details': e.data.get('msg'),
        }
        session['authenticated'] = False
        login_fail_count += 1
        await _set_login_history(last_login_attempt, login_fail_count)
    return web.json_response(result)


async def logout_handler(request: web.Request) -> web.Response:
    session = await get_session(request)
    session.invalidate()
    return web.Response(status=201)


async def webserver_healthcheck(request: web.Request) -> web.Response:
    result = {
        'version': __version__,
        'details': 'Success'
    }
    return web.json_response(result)


async def token_login_handler(request: web.Request) -> web.Response:
    config = request.app['config']

    # Check browser session exists.
    session = await get_session(request)
    if session.get('authenticated', False):
        return web.HTTPBadRequest(text=json.dumps({
            'type': 'https://api.backend.ai/probs/generic-bad-request',
            'title': 'You have already logged in.',
        }), content_type='application/problem+json')

    # Check if auth token is delivered through cookie.
    auth_token_name = config['api'].get('auth_token_name')
    if not auth_token_name:
        return web.HTTPBadRequest(text=json.dumps({
            'type': 'https://api.backend.ai/probs/invalid-api-params',
            'title': 'Auth token name is not defined',
        }), content_type='application/problem+json')
    auth_token = request.cookies.get(auth_token_name)
    if not auth_token:
        return web.HTTPBadRequest(text=json.dumps({
            'type': 'https://api.backend.ai/probs/invalid-api-params',
            'title': 'You must provide cookie-based authentication token',
        }), content_type='application/problem+json')

    # Login with the token.
    # We do not pose consecutive login failure for this handler since
    # user may frequently click edu-api launcher button.
    result: MutableMapping[str, Any] = {
        'authenticated': False,
        'data': None,
    }
    try:
        anon_api_config = APIConfig(
            domain=config['api']['domain'],
            endpoint=config['api']['endpoint'],
            access_key='', secret_key='',  # anonymous session
            user_agent=user_agent,
            skip_sslcert_validation=not config['api'].get('ssl-verify', True),
        )
        assert anon_api_config.is_anonymous
        async with APISession(config=anon_api_config) as api_session:
            # Send X-Forwarded-For header for token authentication with the client IP.
            client_ip = request.headers.get('X-Forwarded-For', request.remote)
            if client_ip:
                _headers = {'X-Forwarded-For': client_ip}
                api_session.aiohttp_session.headers.update(_headers)
            # Instead of email and password, cookie token will be used for auth.
            api_session.aiohttp_session.cookie_jar.update_cookies(request.cookies)
            token = await api_session.User.authorize('fake-email', 'fake-pwd')
            stored_token = {
                'type': 'keypair',
                'access_key': token.content['access_key'],
                'secret_key': token.content['secret_key'],
                'role': token.content['role'],
                'status': token.content.get('status'),
            }
            public_return = {
                'access_key': token.content['access_key'],
                'role': token.content['role'],
                'status': token.content.get('status'),
            }
            session['authenticated'] = True
            session['token'] = stored_token  # store full token
            result['authenticated'] = True
            result['data'] = public_return  # store public info from token
    except BackendClientError as e:
        return web.HTTPBadGateway(text=json.dumps({
            'type': 'https://api.backend.ai/probs/bad-gateway',
            'title': "The proxy target server is inaccessible.",
            'details': str(e),
        }), content_type='application/problem+json')
    except BackendAPIError as e:
        log.info('Authorization failed for token {}: {}', auth_token, e)
        result['authenticated'] = False
        result['data'] = {
            'type': e.data.get('type'),
            'title': e.data.get('title'),
            'details': e.data.get('msg'),
        }
        session['authenticated'] = False
    return web.json_response(result)


async def server_shutdown(app) -> None:
    pass


async def server_cleanup(app) -> None:
    await app['redis'].close()


@aiotools.server
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: Tuple[Any, ...],
) -> AsyncIterator[None]:
    config = args[0]
    app = web.Application()
    app['config'] = config
    redis_url = (
        yarl.URL("redis://host")
        .with_host(config['session']['redis']['host'])
        .with_port(config['session']['redis']['port'])
        .with_password(config['session']['redis'].get('password', None))
        / str(config['session']['redis'].get('db', 0))  # noqa
    )
    keepalive_options = {}
    if hasattr(socket, 'TCP_KEEPIDLE'):
        keepalive_options[socket.TCP_KEEPIDLE] = 20
    if hasattr(socket, 'TCP_KEEPINTVL'):
        keepalive_options[socket.TCP_KEEPINTVL] = 5
    if hasattr(socket, 'TCP_KEEPCNT'):
        keepalive_options[socket.TCP_KEEPCNT] = 3
    app['redis'] = await aioredis.Redis.from_url(
        str(redis_url),
        socket_keepalive=True,
        socket_keepalive_options=keepalive_options,
    )

    if pidx == 0 and config['session'].get('flush_on_startup', False):
        await app['redis'].flushdb()
        log.info('flushed session storage.')
    redis_storage = RedisStorage(
        app['redis'],
        max_age=config['session']['max_age'])

    setup_session(app, redis_storage)
    cors_options = {
        '*': aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            allow_methods='*',
            expose_headers="*",
            allow_headers="*"),
    }
    cors = aiohttp_cors.setup(app, defaults=cors_options)

    anon_web_handler = partial(web_handler, is_anonymous=True)
    anon_web_plugin_handler = partial(web_plugin_handler, is_anonymous=True)

    app.router.add_route('HEAD', '/func/{path:folders/_/tus/upload/.*$}', anon_web_plugin_handler)
    app.router.add_route('PATCH', '/func/{path:folders/_/tus/upload/.*$}', anon_web_plugin_handler)
    app.router.add_route('OPTIONS', '/func/{path:folders/_/tus/upload/.*$}', anon_web_plugin_handler)
    cors.add(app.router.add_route('POST', '/server/login', login_handler))
    cors.add(app.router.add_route('POST', '/server/token-login', token_login_handler))
    cors.add(app.router.add_route('POST', '/server/login-check', login_check_handler))
    cors.add(app.router.add_route('POST', '/server/logout', logout_handler))
    cors.add(app.router.add_route('GET', '/func/ping', webserver_healthcheck))
    cors.add(app.router.add_route('GET', '/func/{path:hanati/user}', anon_web_plugin_handler))
    cors.add(app.router.add_route('GET', '/func/{path:cloud/.*$}', anon_web_plugin_handler))
    cors.add(app.router.add_route('POST', '/func/{path:cloud/.*$}', anon_web_plugin_handler))
    cors.add(app.router.add_route('POST', '/func/{path:auth/signup}', anon_web_plugin_handler))
    cors.add(app.router.add_route('POST', '/func/{path:auth/signout}', web_handler))
    cors.add(app.router.add_route('GET', '/func/{path:stream/kernel/_/events}', web_handler))
    cors.add(app.router.add_route('GET', '/func/{path:stream/session/[^/]+/apps$}', web_handler))
    cors.add(app.router.add_route('GET', '/func/{path:stream/.*$}', websocket_handler))
    cors.add(app.router.add_route('GET', '/func/', anon_web_handler))
    cors.add(app.router.add_route('HEAD', '/func/{path:.*$}', web_handler))
    cors.add(app.router.add_route('GET', '/func/{path:.*$}', web_handler))
    cors.add(app.router.add_route('PUT', '/func/{path:.*$}', web_handler))
    cors.add(app.router.add_route('POST', '/func/{path:.*$}', web_handler))
    cors.add(app.router.add_route('PATCH', '/func/{path:.*$}', web_handler))
    cors.add(app.router.add_route('DELETE', '/func/{path:.*$}', web_handler))
    if config['service']['mode'] == 'webui':
        fallback_handler = console_handler
    elif config['service']['mode'] == 'static':
        fallback_handler = static_handler
    else:
        raise ValueError('Unrecognized service.mode', config['service']['mode'])
    cors.add(app.router.add_route('GET', '/{path:.*$}', fallback_handler))

    app.on_shutdown.append(server_shutdown)
    app.on_cleanup.append(server_cleanup)

    ssl_ctx = None
    if 'ssl-enabled' in config['service'] and config['service']['ssl-enabled']:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            str(config['service']['ssl-cert']),
            str(config['service']['ssl-privkey']),
        )

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        str(config['service']['ip']),
        config['service']['port'],
        backlog=1024,
        reuse_port=True,
        ssl_context=ssl_ctx,
    )
    await site.start()
    log.info('started.')

    try:
        yield
    finally:
        log.info('shutting down...')
        await runner.cleanup()


@click.command()
@click.option('-f', '--config', 'config_path',
              type=click.Path(exists=True),
              default='webserver.conf',
              help='The configuration file to use.')
@click.option('--debug', is_flag=True,
              default=False,
              help='Use more verbose logging.')
def main(config_path: str, debug: bool) -> None:
    config = toml.loads(Path(config_path).read_text(encoding='utf-8'))
    config['debug'] = debug
    if config['debug']:
        debugFlag = 'DEBUG'
    else:
        debugFlag = 'INFO'
    setproctitle(f"backend.ai: webserver "
                 f"{config['service']['ip']}:{config['service']['port']}")

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'colored': {
                '()': 'coloredlogs.ColoredFormatter',
                'format': '%(asctime)s %(levelname)s %(name)s '
                          '[%(process)d] %(message)s',
                'field_styles': {'levelname': {'color': 248, 'bold': True},
                                 'name': {'color': 246, 'bold': False},
                                 'process': {'color': 'cyan'},
                                 'asctime': {'color': 240}},
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'colored',
                'stream': 'ext://sys.stderr',
            },
            'null': {
                'class': 'logging.NullHandler',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': debugFlag,
            },
        },
    })
    log.info('Backend.AI Web Server {0}', __version__)
    log.info('runtime: {0}', sys.prefix)
    log_config = logging.getLogger('ai.backend.web.config')
    log_config.debug('debug mode enabled.')
    print('== Web Server configuration ==')
    pprint(config)
    log.info('serving at {0}:{1}', config['service']['ip'], config['service']['port'])

    try:
        uvloop.install()
        aiotools.start_server(
            server_main,
            num_workers=min(4, os.cpu_count() or 1),
            args=(config,),
        )
    finally:
        log.info('terminated.')


if __name__ == '__main__':
    main()
