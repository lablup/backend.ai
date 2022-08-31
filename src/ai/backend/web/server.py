import asyncio
import json
import logging
import logging.config
import os
import re
import socket
import ssl
import sys
import time
from functools import partial
from pathlib import Path
from pprint import pprint
from typing import Any, AsyncIterator, MutableMapping, Tuple

import aiohttp_cors
import aiotools
import click
import jinja2
import tomli
import uvloop
import yarl
from aiohttp import web
from aiohttp_session import get_session
from aiohttp_session import setup as setup_session
from aiohttp_session.redis_storage import RedisStorage
from aioredis import Redis as AioRedisLegacy
from redis.asyncio import Redis
from setproctitle import setproctitle

from ai.backend.client.config import APIConfig
from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.session import AsyncSession as APISession

from . import __version__, user_agent
from .config import config_iv
from .logging import BraceStyleAdapter
from .proxy import decrypt_payload, web_handler, web_plugin_handler, websocket_handler
from .template import toml_scalar

log = BraceStyleAdapter(logging.getLogger("ai.backend.web.server"))

cache_patterns = {
    r"\.(?:manifest|appcache|html?|xml|json|ini|toml)$": {
        "Cache-Control": "no-store",
    },
    r"(?:backend.ai-webui.js)$": {
        "Cache-Control": "no-store",
    },
    r"\.(?:jpg|jpeg|gif|png|ico|cur|gz|svg|svgz|mp4|ogg|ogv|webm|htc|woff|woff2)$": {
        "Cache-Control": "max-age=259200, public",
    },
    r"\.(?:css|js)$": {
        "Cache-Control": "max-age=86400, public, must-revalidate, proxy-revalidate",
    },
    r"\.(?:py|log?|txt)$": {
        "Cache-Control": "no-store",
    },
}
_cache_patterns = {re.compile(k): v for k, v in cache_patterns.items()}


def apply_cache_headers(response: web.StreamResponse, path: str) -> web.StreamResponse:
    for regex, headers in _cache_patterns.items():
        mo = regex.search(path)
        if mo is not None:
            response.headers.update(headers)
            break
    return response


async def static_handler(request: web.Request) -> web.StreamResponse:
    request_path = request.match_info["path"]
    static_path = request.app["config"]["service"]["static_path"]
    file_path = (static_path / request_path).resolve()
    try:
        file_path.relative_to(static_path)
    except (ValueError, FileNotFoundError):
        return web.HTTPNotFound(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/generic-not-found",
                    "title": "Not Found",
                }
            ),
            content_type="application/problem+json",
        )
    if file_path.is_file():
        return apply_cache_headers(web.FileResponse(file_path), request_path)
    return web.HTTPNotFound(
        text=json.dumps(
            {
                "type": "https://api.backend.ai/probs/generic-not-found",
                "title": "Not Found",
            }
        ),
        content_type="application/problem+json",
    )


async def config_ini_handler(request: web.Request) -> web.Response:
    config = request.app["config"]
    scheme = config["service"]["force_endpoint_protocol"]
    if scheme is None:
        scheme = request.scheme
    j2env: jinja2.Environment = request.app["j2env"]
    tpl = j2env.get_template("config_ini.toml.j2")
    config_content = tpl.render(
        {
            "endpoint_url": f"{scheme}://{request.host}",  # must be absolute
            "config": config,
        }
    )
    return web.Response(text=config_content, content_type="text/plain")


async def config_toml_handler(request: web.Request) -> web.Response:
    config = request.app["config"]
    scheme = config["service"]["force_endpoint_protocol"]
    if scheme is None:
        scheme = request.scheme
    j2env: jinja2.Environment = request.app["j2env"]
    tpl = j2env.get_template("config.toml.j2")
    config_content = tpl.render(
        {
            "endpoint_url": f"{scheme}://{request.host}",  # must be absolute
            "config": config,
        }
    )
    return web.Response(text=config_content, content_type="text/plain")


async def console_handler(request: web.Request) -> web.StreamResponse:
    request_path = request.match_info["path"]
    config = request.app["config"]
    static_path = config["service"]["static_path"]
    file_path = (static_path / request_path).resolve()
    # SECURITY: only allow reading files under static_path
    try:
        file_path.relative_to(static_path)
    except (ValueError, FileNotFoundError):
        return web.HTTPNotFound(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/generic-not-found",
                    "title": "Not Found",
                }
            ),
            content_type="application/problem+json",
        )
    if file_path.is_file():
        return apply_cache_headers(web.FileResponse(file_path), request_path)
    # Fallback to index.html to support the URL routing for single-page application.
    return apply_cache_headers(web.FileResponse(static_path / "index.html"), "index.html")


async def login_check_handler(request: web.Request) -> web.Response:
    session = await get_session(request)
    authenticated = bool(session.get("authenticated", False))
    public_data = None
    if authenticated:
        stored_token = session["token"]
        public_data = {
            "access_key": stored_token["access_key"],
            "role": stored_token["role"],
            "status": stored_token.get("status"),
        }
    return web.json_response(
        {
            "authenticated": authenticated,
            "data": public_data,
            "session_id": session.identity,  # temporary wsproxy interop patch
        }
    )


async def login_handler(request: web.Request) -> web.Response:
    config = request.app["config"]
    session = await get_session(request)
    if session.get("authenticated", False):
        return web.HTTPBadRequest(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/generic-bad-request",
                    "title": "You have already logged in.",
                }
            ),
            content_type="application/problem+json",
        )
    try:
        creds = json.loads(request["payload"])
    except json.JSONDecodeError as e:
        log.error("Login: JSON decoding error: {}", e)
        creds = {}
    if "username" not in creds or not creds["username"]:
        return web.HTTPBadRequest(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/invalid-api-params",
                    "title": "You must provide the username field.",
                }
            ),
            content_type="application/problem+json",
        )
    if "password" not in creds or not creds["password"]:
        return web.HTTPBadRequest(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/invalid-api-params",
                    "title": "You must provide the password field.",
                }
            ),
            content_type="application/problem+json",
        )
    result: MutableMapping[str, Any] = {
        "authenticated": False,
        "data": None,
    }

    async def _get_login_history():
        login_history = await request.app["redis"].get(
            f'login_history_{creds["username"]}',
        )
        if not login_history:
            login_history = {
                "last_login_attempt": 0,
                "login_fail_count": 0,
            }
        else:
            login_history = json.loads(login_history)
        if login_history["last_login_attempt"] < 0:
            login_history["last_login_attempt"] = 0
        if login_history["login_fail_count"] < 0:
            login_history["login_fail_count"] = 0
        return login_history

    async def _set_login_history(last_login_attempt, login_fail_count):
        """
        Set login history per email (not in browser session).
        """
        key = f'login_history_{creds["username"]}'
        value = json.dumps(
            {
                "last_login_attempt": last_login_attempt,
                "login_fail_count": login_fail_count,
            }
        )
        await request.app["redis"].set(key, value)

    # Block login if there are too many consecutive failed login attempts.
    BLOCK_TIME = config["session"]["login_block_time"]
    ALLOWED_FAIL_COUNT = config["session"]["login_allowed_fail_count"]
    login_time = time.time()
    login_history = await _get_login_history()
    last_login_attempt = login_history.get("last_login_attempt", 0)
    login_fail_count = login_history.get("login_fail_count", 0)
    if login_time - last_login_attempt > BLOCK_TIME:
        # If last attempt is far past, allow login again.
        login_fail_count = 0
    last_login_attempt = login_time
    if login_fail_count >= ALLOWED_FAIL_COUNT:
        log.info(
            "Too many consecutive login attempts for {}: {}",
            creds["username"],
            login_fail_count,
        )
        await _set_login_history(last_login_attempt, login_fail_count)
        return web.HTTPTooManyRequests(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/too-many-requests",
                    "title": "Too many failed login attempts",
                }
            ),
            content_type="application/problem+json",
        )

    try:
        anon_api_config = APIConfig(
            domain=config["api"]["domain"],
            endpoint=config["api"]["endpoint"][0],
            access_key="",
            secret_key="",  # anonymous session
            user_agent=user_agent,
            skip_sslcert_validation=not config["api"]["ssl_verify"],
        )
        assert anon_api_config.is_anonymous
        async with APISession(config=anon_api_config) as api_session:
            token = await api_session.User.authorize(creds["username"], creds["password"])
            stored_token = {
                "type": "keypair",
                "access_key": token.content["access_key"],
                "secret_key": token.content["secret_key"],
                "role": token.content["role"],
                "status": token.content.get("status"),
            }
            public_return = {
                "access_key": token.content["access_key"],
                "role": token.content["role"],
                "status": token.content.get("status"),
            }
            session["authenticated"] = True
            session["token"] = stored_token  # store full token
            result["authenticated"] = True
            result["data"] = public_return  # store public info from token
            login_fail_count = 0
            await _set_login_history(last_login_attempt, login_fail_count)
    except BackendClientError as e:
        # This is error, not failed login, so we should not update login history.
        return web.HTTPBadGateway(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/bad-gateway",
                    "title": "The proxy target server is inaccessible.",
                    "details": str(e),
                }
            ),
            content_type="application/problem+json",
        )
    except BackendAPIError as e:
        log.info("Authorization failed for {}: {}", creds["username"], e)
        result["authenticated"] = False
        result["data"] = {
            "type": e.data.get("type"),
            "title": e.data.get("title"),
            "details": e.data.get("msg"),
        }
        session["authenticated"] = False
        login_fail_count += 1
        await _set_login_history(last_login_attempt, login_fail_count)
    return web.json_response(result)


async def logout_handler(request: web.Request) -> web.Response:
    session = await get_session(request)
    session.invalidate()
    return web.Response(status=201)


async def webserver_healthcheck(_: web.Request) -> web.Response:
    result = {
        "version": __version__,
        "details": "Success",
    }
    return web.json_response(result)


async def token_login_handler(request: web.Request) -> web.Response:
    config = request.app["config"]

    # Check browser session exists.
    session = await get_session(request)
    if session.get("authenticated", False):
        return web.HTTPBadRequest(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/generic-bad-request",
                    "title": "You have already logged in.",
                }
            ),
            content_type="application/problem+json",
        )

    # Check if auth token is delivered through cookie.
    auth_token_name = config["api"]["auth_token_name"]
    auth_token = request.cookies.get(auth_token_name)
    if not auth_token:
        return web.HTTPBadRequest(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/invalid-api-params",
                    "title": "You must provide cookie-based authentication token",
                }
            ),
            content_type="application/problem+json",
        )

    # Login with the token.
    # We do not pose consecutive login failure for this handler since
    # user may frequently click edu-api launcher button.
    result: MutableMapping[str, Any] = {
        "authenticated": False,
        "data": None,
    }
    try:
        anon_api_config = APIConfig(
            domain=config["api"]["domain"],
            endpoint=config["api"]["endpoint"][0],
            access_key="",
            secret_key="",  # anonymous session
            user_agent=user_agent,
            skip_sslcert_validation=not config["api"]["ssl_verify"],
        )
        assert anon_api_config.is_anonymous
        async with APISession(config=anon_api_config) as api_session:
            # Send X-Forwarded-For header for token authentication with the client IP.
            client_ip = request.headers.get("X-Forwarded-For", request.remote)
            if client_ip:
                _headers = {"X-Forwarded-For": client_ip}
                api_session.aiohttp_session.headers.update(_headers)
            # Instead of email and password, cookie token will be used for auth.
            api_session.aiohttp_session.cookie_jar.update_cookies(request.cookies)
            token = await api_session.User.authorize("fake-email", "fake-pwd")
            stored_token = {
                "type": "keypair",
                "access_key": token.content["access_key"],
                "secret_key": token.content["secret_key"],
                "role": token.content["role"],
                "status": token.content.get("status"),
            }
            public_return = {
                "access_key": token.content["access_key"],
                "role": token.content["role"],
                "status": token.content.get("status"),
            }
            session["authenticated"] = True
            session["token"] = stored_token  # store full token
            result["authenticated"] = True
            result["data"] = public_return  # store public info from token
    except BackendClientError as e:
        return web.HTTPBadGateway(
            text=json.dumps(
                {
                    "type": "https://api.backend.ai/probs/bad-gateway",
                    "title": "The proxy target server is inaccessible.",
                    "details": str(e),
                }
            ),
            content_type="application/problem+json",
        )
    except BackendAPIError as e:
        log.info("Authorization failed for token {}: {}", auth_token, e)
        result["authenticated"] = False
        result["data"] = {
            "type": e.data.get("type"),
            "title": e.data.get("title"),
            "details": e.data.get("msg"),
        }
        session["authenticated"] = False
    return web.json_response(result)


async def server_shutdown(app) -> None:
    pass


async def server_cleanup(app) -> None:
    await app["redis"].close()


@aiotools.server
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: Tuple[Any, ...],
) -> AsyncIterator[None]:
    config = args[0]
    app = web.Application(middlewares=[decrypt_payload])
    app["config"] = config
    j2env = jinja2.Environment(
        extensions=[
            "ai.backend.web.template.TOMLField",
            "ai.backend.web.template.TOMLStringListField",
        ],
        loader=jinja2.PackageLoader("ai.backend.web", "templates"),
    )
    j2env.filters["toml_scalar"] = toml_scalar
    app["j2env"] = j2env

    redis_url = yarl.URL("redis://host").with_host(config["session"]["redis"]["host"]).with_port(
        config["session"]["redis"]["port"]
    ).with_password(config["session"]["redis"]["password"]) / str(config["session"]["redis"]["db"])
    keepalive_options = {}
    if hasattr(socket, "TCP_KEEPIDLE"):
        keepalive_options[socket.TCP_KEEPIDLE] = 20
    if hasattr(socket, "TCP_KEEPINTVL"):
        keepalive_options[socket.TCP_KEEPINTVL] = 5
    if hasattr(socket, "TCP_KEEPCNT"):
        keepalive_options[socket.TCP_KEEPCNT] = 3
    app["redis"] = await Redis.from_url(
        str(redis_url),
        socket_keepalive=True,
        socket_keepalive_options=keepalive_options,
    )
    # FIXME: remove after aio-libs/aiohttp-session#704 is merged
    aioredis_legacy_client = await AioRedisLegacy.from_url(
        str(redis_url),
        socket_keepalive=True,
        socket_keepalive_options=keepalive_options,
    )

    if pidx == 0 and config["session"]["flush_on_startup"]:
        await app["redis"].flushdb()
        log.info("flushed session storage.")
    redis_storage = RedisStorage(
        # FIXME: replace to app['redis'] after aio-libs/aiohttp-session#704 is merged
        aioredis_legacy_client,
        max_age=config["session"]["max_age"],
    )

    setup_session(app, redis_storage)
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True, allow_methods="*", expose_headers="*", allow_headers="*"
        ),
    }
    cors = aiohttp_cors.setup(app, defaults=cors_options)

    anon_web_handler = partial(web_handler, is_anonymous=True)
    anon_web_plugin_handler = partial(web_plugin_handler, is_anonymous=True)

    app.router.add_route("HEAD", "/func/{path:folders/_/tus/upload/.*$}", anon_web_plugin_handler)
    app.router.add_route("PATCH", "/func/{path:folders/_/tus/upload/.*$}", anon_web_plugin_handler)
    app.router.add_route(
        "OPTIONS", "/func/{path:folders/_/tus/upload/.*$}", anon_web_plugin_handler
    )
    cors.add(app.router.add_route("POST", "/server/login", login_handler))
    cors.add(app.router.add_route("POST", "/server/token-login", token_login_handler))
    cors.add(app.router.add_route("POST", "/server/login-check", login_check_handler))
    cors.add(app.router.add_route("POST", "/server/logout", logout_handler))
    cors.add(app.router.add_route("GET", "/func/ping", webserver_healthcheck))
    cors.add(app.router.add_route("GET", "/func/{path:hanati/user}", anon_web_plugin_handler))
    cors.add(app.router.add_route("GET", "/func/{path:cloud/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("POST", "/func/{path:cloud/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("POST", "/func/{path:saml/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("POST", "/func/{path:auth/signup}", anon_web_plugin_handler))
    cors.add(app.router.add_route("POST", "/func/{path:auth/signout}", web_handler))
    cors.add(app.router.add_route("GET", "/func/{path:stream/kernel/_/events}", web_handler))
    cors.add(app.router.add_route("GET", "/func/{path:stream/session/[^/]+/apps$}", web_handler))
    cors.add(app.router.add_route("GET", "/func/{path:stream/.*$}", websocket_handler))
    cors.add(app.router.add_route("GET", "/func/", anon_web_handler))
    cors.add(app.router.add_route("HEAD", "/func/{path:.*$}", web_handler))
    cors.add(app.router.add_route("GET", "/func/{path:.*$}", web_handler))
    cors.add(app.router.add_route("PUT", "/func/{path:.*$}", web_handler))
    cors.add(app.router.add_route("POST", "/func/{path:.*$}", web_handler))
    cors.add(app.router.add_route("PATCH", "/func/{path:.*$}", web_handler))
    cors.add(app.router.add_route("DELETE", "/func/{path:.*$}", web_handler))
    cors.add(app.router.add_route("GET", "/pipeline/{path:.*$}", web_handler))
    cors.add(app.router.add_route("PUT", "/pipeline/{path:.*$}", web_handler))
    cors.add(app.router.add_route("POST", "/pipeline/{path:.*$}", web_handler))
    cors.add(app.router.add_route("PATCH", "/pipeline/{path:.*$}", web_handler))
    cors.add(app.router.add_route("DELETE", "/pipeline/{path:.*$}", web_handler))
    if config["service"]["mode"] == "webui":
        cors.add(app.router.add_route("GET", "/config.ini", config_ini_handler))
        cors.add(app.router.add_route("GET", "/config.toml", config_toml_handler))
        fallback_handler = console_handler
    elif config["service"]["mode"] == "static":
        fallback_handler = static_handler
    else:
        raise ValueError("Unrecognized service.mode", config["service"]["mode"])
    cors.add(app.router.add_route("GET", "/{path:.*$}", fallback_handler))

    app.on_shutdown.append(server_shutdown)
    app.on_cleanup.append(server_cleanup)

    ssl_ctx = None
    if config["service"]["ssl_enabled"]:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            str(config["service"]["ssl_cert"]),
            str(config["service"]["ssl_privkey"]),
        )

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        str(config["service"]["ip"]),
        config["service"]["port"],
        backlog=1024,
        reuse_port=True,
        ssl_context=ssl_ctx,
    )
    await site.start()
    log.info("started.")

    try:
        yield
    finally:
        log.info("shutting down...")
        await runner.cleanup()


@click.command()
@click.option(
    "-f",
    "--config",
    "config_path",
    type=click.Path(exists=True),
    default="webserver.conf",
    help="The configuration file to use.",
)
@click.option("--debug", is_flag=True, default=False, help="Use more verbose logging.")
def main(config_path: str, debug: bool) -> None:
    raw_config = tomli.loads(Path(config_path).read_text(encoding="utf-8"))
    config = config_iv.check(raw_config)
    config["debug"] = debug
    if config["debug"]:
        debugFlag = "DEBUG"
    else:
        debugFlag = "INFO"
    setproctitle(f"backend.ai: webserver " f"{config['service']['ip']}:{config['service']['port']}")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "colored": {
                    "()": "coloredlogs.ColoredFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s " "[%(process)d] %(message)s",
                    "field_styles": {
                        "levelname": {"color": 248, "bold": True},
                        "name": {"color": 246, "bold": False},
                        "process": {"color": "cyan"},
                        "asctime": {"color": 240},
                    },
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "colored",
                    "stream": "ext://sys.stderr",
                },
                "null": {
                    "class": "logging.NullHandler",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console"],
                    "level": debugFlag,
                },
            },
        }
    )
    log.info("Backend.AI Web Server {0}", __version__)
    log.info("runtime: {0}", sys.prefix)
    log_config = logging.getLogger("ai.backend.web.config")
    log_config.debug("debug mode enabled.")
    if debug:
        print("== Web Server configuration ==")
        pprint(config)
    log.info("serving at {0}:{1}", config["service"]["ip"], config["service"]["port"])

    try:
        uvloop.install()
        aiotools.start_server(
            server_main,
            num_workers=min(4, os.cpu_count() or 1),
            args=(config,),
        )
    finally:
        log.info("terminated.")


if __name__ == "__main__":
    main()
