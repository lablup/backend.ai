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
import traceback
from functools import partial
from pathlib import Path
from pprint import pprint
from typing import Any, AsyncIterator, MutableMapping, Tuple

import aiohttp_cors
import aiotools
import click
import jinja2
import tomli
from aiohttp import web
from setproctitle import setproctitle

from ai.backend.client.config import APIConfig
from ai.backend.client.exceptions import BackendAPIError, BackendClientError
from ai.backend.client.session import AsyncSession as APISession
from ai.backend.common import config, redis_helper
from ai.backend.common.logging import BraceStyleAdapter, Logger
from ai.backend.common.types import LogSeverity
from ai.backend.common.web.session import extra_config_headers, get_session
from ai.backend.common.web.session import setup as setup_session
from ai.backend.common.web.session.redis_storage import RedisStorage

from . import __version__, user_agent
from .auth import fill_forwarding_hdrs_to_api_session, get_client_ip
from .config import config_iv
from .proxy import decrypt_payload, web_handler, web_plugin_handler, websocket_handler
from .stats import WebStats, track_active_handlers, view_stats
from .template import toml_scalar

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
    stats: WebStats = request.app["stats"]
    stats.active_static_handlers.add(asyncio.current_task())  # type: ignore
    request_path = request.match_info["path"]
    static_path = request.app["config"]["service"]["static_path"]
    file_path = (static_path / request_path).resolve()
    try:
        file_path.relative_to(static_path)
    except (ValueError, FileNotFoundError):
        return web.HTTPNotFound(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/generic-not-found",
                "title": "Not Found",
            }),
            content_type="application/problem+json",
        )
    if file_path.is_file():
        return apply_cache_headers(web.FileResponse(file_path), request_path)
    return web.HTTPNotFound(
        text=json.dumps({
            "type": "https://api.backend.ai/probs/generic-not-found",
            "title": "Not Found",
        }),
        content_type="application/problem+json",
    )


async def config_ini_handler(request: web.Request) -> web.Response:
    stats: WebStats = request.app["stats"]
    stats.active_config_handlers.add(asyncio.current_task())  # type: ignore
    config = request.app["config"]
    scheme = config["service"]["force_endpoint_protocol"]
    if scheme is None:
        scheme = request.scheme
    j2env: jinja2.Environment = request.app["j2env"]
    tpl = j2env.get_template("config_ini.toml.j2")
    config_content = tpl.render({
        "endpoint_url": f"{scheme}://{request.host}",  # must be absolute
        "config": config,
    })
    return web.Response(text=config_content, content_type="text/plain")


async def config_toml_handler(request: web.Request) -> web.Response:
    stats: WebStats = request.app["stats"]
    stats.active_config_handlers.add(asyncio.current_task())  # type: ignore
    config = request.app["config"]
    scheme = config["service"]["force_endpoint_protocol"]
    if scheme is None:
        scheme = request.scheme
    j2env: jinja2.Environment = request.app["j2env"]
    tpl = j2env.get_template("config.toml.j2")
    config_content = tpl.render({
        "endpoint_url": f"{scheme}://{request.host}",  # must be absolute
        "config": config,
    })
    return web.Response(text=config_content, content_type="text/plain")


async def console_handler(request: web.Request) -> web.StreamResponse:
    stats: WebStats = request.app["stats"]
    stats.active_webui_handlers.add(asyncio.current_task())  # type: ignore
    request_path = request.match_info["path"]
    config = request.app["config"]
    static_path = config["service"]["static_path"]
    file_path = (static_path / request_path).resolve()
    # SECURITY: only allow reading files under static_path
    try:
        file_path.relative_to(static_path)
    except (ValueError, FileNotFoundError):
        return web.HTTPNotFound(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/generic-not-found",
                "title": "Not Found",
            }),
            content_type="application/problem+json",
        )
    if file_path.is_file():
        return apply_cache_headers(web.FileResponse(file_path), request_path)
    # Fallback to index.html to support the URL routing for single-page application.
    return apply_cache_headers(web.FileResponse(static_path / "index.html"), "index.html")


async def update_password_no_auth(request: web.Request) -> web.Response:
    config = request.app["config"]
    client_ip = get_client_ip(request)
    try:
        text = await request.text()
        creds = json.loads(text)
    except json.JSONDecodeError as e:
        log.error("Login: JSON decoding error: {}", e)
        creds = {}

    def _check_params(param_names: list[str]) -> web.Response | None:
        for param in param_names:
            if creds.get(param) is None:
                return web.HTTPBadRequest(
                    text=json.dumps({
                        "type": "https://api.backend.ai/probs/invalid-api-params",
                        "title": f"You must provide the {param} field.",
                    }),
                    content_type="application/problem+json",
                )
        return None

    if (fail_resp := _check_params(["username", "current_password", "new_password"])) is not None:
        return fail_resp

    result: dict[str, Any] = {
        "data": None,
        "password_changed_at": None,
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
            fill_forwarding_hdrs_to_api_session(request, api_session)
            result = await api_session.Auth.update_password_no_auth(
                config["api"]["domain"],
                creds["username"],
                creds["current_password"],
                creds["new_password"],
            )
            log.info(
                "UPDATE_PASSWORD_NO_AUTH: Authorization succeeded for (email:{}, ip:{})",
                creds["username"],
                client_ip,
            )
    except BackendClientError as e:
        # This is error, not failed login, so we should not update login history.
        return web.HTTPBadGateway(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
                "details": str(e),
            }),
            content_type="application/problem+json",
        )
    except BackendAPIError as e:
        log.info(
            "LOGIN_HANDLER: Authorization failed (email:{}, ip:{}) - {}",
            creds["username"],
            client_ip,
            e,
        )
        result["data"] = {
            "type": e.data.get("type"),
            "title": e.data.get("title"),
            "details": e.data.get("msg"),
        }
    return web.json_response(result)


async def login_check_handler(request: web.Request) -> web.Response:
    session = await get_session(request)
    stats: WebStats = request.app["stats"]
    stats.active_login_check_handlers.add(asyncio.current_task())  # type: ignore
    authenticated = bool(session.get("authenticated", False))
    public_data = None
    if authenticated:
        stored_token = session["token"]
        public_data = {
            "access_key": stored_token["access_key"],
            "role": stored_token["role"],
            "status": stored_token.get("status"),
        }
    return web.json_response({
        "authenticated": authenticated,
        "data": public_data,
        "session_id": session.identity,  # temporary wsproxy interop patch
    })


async def login_handler(request: web.Request) -> web.Response:
    config = request.app["config"]
    stats: WebStats = request.app["stats"]
    stats.active_login_handlers.add(asyncio.current_task())  # type: ignore
    session = await get_session(request)
    if session.get("authenticated", False):
        return web.HTTPBadRequest(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/generic-bad-request",
                "title": "You have already logged in.",
            }),
            content_type="application/problem+json",
        )
    request_headers = extra_config_headers.check(request.headers)
    secure_context = request_headers.get("X-BackendAI-Encoded", None)
    client_ip = get_client_ip(request)
    if not secure_context:
        # For non-encrypted requests, just read the body as-is.
        # Encrypted requests are handled by the `decrypt_payload` middleware.
        request["payload"] = await request.text()
    try:
        creds = json.loads(request["payload"])
    except json.JSONDecodeError as e:
        log.error("Login: JSON decoding error: {}", e)
        creds = {}
    if "username" not in creds or not creds["username"]:
        return web.HTTPBadRequest(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/invalid-api-params",
                "title": "You must provide the username field.",
            }),
            content_type="application/problem+json",
        )
    if "password" not in creds or not creds["password"]:
        return web.HTTPBadRequest(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/invalid-api-params",
                "title": "You must provide the password field.",
            }),
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
        value = json.dumps({
            "last_login_attempt": last_login_attempt,
            "login_fail_count": login_fail_count,
        })
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
            "LOGIN_HANDLER: Too many consecutive login fails (email:{}, count:{}, ip:{})",
            creds["username"],
            login_fail_count,
            client_ip,
        )
        await _set_login_history(last_login_attempt, login_fail_count)
        return web.HTTPTooManyRequests(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/too-many-requests",
                "title": "Too many failed login attempts",
            }),
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
            fill_forwarding_hdrs_to_api_session(request, api_session)
            extra_args = {}
            extra_keys = set(creds.keys()) ^ {"username", "password"}
            for extra_key in extra_keys:
                extra_args[extra_key] = creds[extra_key]
            token = await api_session.User.authorize(
                creds["username"], creds["password"], extra_args=extra_args
            )
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
            log.info(
                "LOGIN_HANDLER: Authorization succeeded for (email:{}, ip:{})",
                creds["username"],
                client_ip,
            )
    except BackendClientError as e:
        # This is error, not failed login, so we should not update login history.
        return web.HTTPBadGateway(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
                "details": str(e),
            }),
            content_type="application/problem+json",
        )
    except BackendAPIError as e:
        log.info(
            "LOGIN_HANDLER: Authorization failed (email:{}, ip:{}) - {}",
            creds["username"],
            client_ip,
            e,
        )
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
    stats: WebStats = request.app["stats"]
    stats.active_logout_handlers.add(asyncio.current_task())  # type: ignore
    session = await get_session(request)
    session.invalidate()
    return web.HTTPOk()


async def webserver_healthcheck(request: web.Request) -> web.Response:
    stats: WebStats = request.app["stats"]
    stats.active_healthcheck_handlers.add(asyncio.current_task())  # type: ignore
    result = {
        "version": __version__,
        "details": "Success",
    }
    return web.json_response(result)


async def token_login_handler(request: web.Request) -> web.Response:
    config = request.app["config"]
    stats: WebStats = request.app["stats"]
    stats.active_token_login_handlers.add(asyncio.current_task())  # type: ignore

    # Check browser session exists.
    session = await get_session(request)
    if session.get("authenticated", False):
        return web.HTTPBadRequest(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/generic-bad-request",
                "title": "You have already logged in.",
            }),
            content_type="application/problem+json",
        )

    # Check if auth token is delivered via request body or cookie.
    rqst_data: dict[str, Any] = await request.json()
    auth_token_name = config["api"]["auth_token_name"]
    auth_token = rqst_data.get(auth_token_name)
    if not auth_token:
        auth_token = request.cookies.get(auth_token_name)
    if not auth_token:
        return web.HTTPBadRequest(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/invalid-api-params",
                "title": "You must provide cookie-based authentication token",
            }),
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
            fill_forwarding_hdrs_to_api_session(request, api_session)
            # Instead of email and password, token will be used for user auth.
            api_session.aiohttp_session.cookie_jar.update_cookies(request.cookies)
            extra_args = {**rqst_data, auth_token_name: auth_token}
            # The purpose of token login is to authenticate a client, typically a browser, using a
            # separate token referred to as `sToken`, rather than using user's email and password.
            # However, the `api_session.User.authorize` SDK requires email and password as
            # parameters, so we just pass fake (arbitrary) email and password which are placeholders
            # in token-based login. Each authorize hook plugin will deal with various type of
            # `sToken` and related parameters to authorize a user. In this process, email and
            # password do not play any role.
            token = await api_session.User.authorize(
                "fake-email", "fake-pwd", extra_args=extra_args
            )
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
            text=json.dumps({
                "type": "https://api.backend.ai/probs/bad-gateway",
                "title": "The proxy target server is inaccessible.",
                "details": str(e),
            }),
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
async def server_main_logwrapper(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    _args: Tuple[Any, ...],
) -> AsyncIterator[None]:
    setproctitle(f"backend.ai: webserver worker-{pidx}")
    log_endpoint = _args[1]
    logger = Logger(_args[0]["logging"], is_master=False, log_endpoint=log_endpoint)
    try:
        with logger:
            async with server_main(loop, pidx, _args):
                yield
    except Exception:
        traceback.print_exc()


@aiotools.server
async def server_main(
    loop: asyncio.AbstractEventLoop,
    pidx: int,
    args: Tuple[Any, ...],
) -> AsyncIterator[None]:
    config = args[0]
    app = web.Application(middlewares=[decrypt_payload, track_active_handlers])
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

    keepalive_options = {}
    if (_TCP_KEEPIDLE := getattr(socket, "TCP_KEEPIDLE", None)) is not None:
        keepalive_options[_TCP_KEEPIDLE] = 20
    if (_TCP_KEEPINTVL := getattr(socket, "TCP_KEEPINTVL", None)) is not None:
        keepalive_options[_TCP_KEEPINTVL] = 5
    if (_TCP_KEEPCNT := getattr(socket, "TCP_KEEPCNT", None)) is not None:
        keepalive_options[_TCP_KEEPCNT] = 3

    app["redis"] = redis_helper.get_redis_object(
        config["session"]["redis"],
        name="web.session",
        socket_keepalive=True,
        socket_keepalive_options=keepalive_options,
    ).client

    if pidx == 0 and config["session"]["flush_on_startup"]:
        await app["redis"].flushdb()
        log.info("flushed session storage.")

    redis_storage = RedisStorage(
        app["redis"],
        max_age=config["session"]["max_age"],
    )

    setup_session(app, redis_storage)
    cors_options = {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True, allow_methods="*", expose_headers="*", allow_headers="*"
        ),
    }
    cors = aiohttp_cors.setup(app, defaults=cors_options)

    app["stats"] = WebStats()

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
    cors.add(
        app.router.add_route("POST", "/server/update-password-no-auth", update_password_no_auth)
    )
    cors.add(app.router.add_route("GET", "/stats", view_stats))
    cors.add(app.router.add_route("GET", "/func/ping", webserver_healthcheck))
    cors.add(app.router.add_route("GET", "/func/{path:cloud/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("POST", "/func/{path:cloud/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("POST", "/func/{path:custom-auth/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("GET", "/func/{path:custom-auth/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("GET", "/func/{path:openid/.*$}", anon_web_plugin_handler))
    cors.add(app.router.add_route("POST", "/func/{path:openid/.*$}", anon_web_plugin_handler))
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
    cors.add(app.router.add_route("GET", "/pipeline/{path:stream/.*$}", websocket_handler))
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

    async def on_prepare(request, response):
        # Remove "Server" header for a security reason.
        response.headers.popall("Server", None)

    app.on_response_prepare.append(on_prepare)

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
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="webserver.conf",
    help="The configuration file to use.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Set the logging level to DEBUG",
)
@click.option(
    "--log-level",
    type=click.Choice([*LogSeverity], case_sensitive=False),
    default=LogSeverity.INFO,
    help="Set the logging verbosity level",
)
@click.pass_context
def main(
    ctx: click.Context,
    config_path: Path,
    log_level: LogSeverity,
    debug: bool,
) -> None:
    """Start the webui host service as a foreground process."""
    # Delete this part when you remove --debug option
    raw_cfg = tomli.loads(Path(config_path).read_text(encoding="utf-8"))

    if debug:
        log_level = LogSeverity.DEBUG
    config.override_key(raw_cfg, ("debug", "enabled"), log_level == LogSeverity.DEBUG)
    config.override_key(raw_cfg, ("logging", "level"), log_level)
    config.override_key(raw_cfg, ("logging", "pkg-ns", "ai.backend"), log_level)

    cfg = config.check(raw_cfg, config_iv)
    config.set_if_not_set(cfg, ("pipeline", "frontend-endpoint"), cfg["pipeline"]["endpoint"])

    if ctx.invoked_subcommand is None:
        cfg["webserver"]["pid-file"].write_text(str(os.getpid()))
        ipc_base_path = cfg["webserver"]["ipc-base-path"]
        log_sockpath = ipc_base_path / f"webserver-logger-{os.getpid()}.sock"
        log_sockpath.parent.mkdir(parents=True, exist_ok=True)
        log_endpoint = f"ipc://{log_sockpath}"
        cfg["logging"]["endpoint"] = log_endpoint
        try:
            logger = Logger(cfg["logging"], is_master=True, log_endpoint=log_endpoint)
            with logger:
                setproctitle(
                    f"backend.ai: webserver {cfg['service']['ip']}:{cfg['service']['port']}"
                )
                log.info("Backend.AI Web Server {0}", __version__)
                log.info("runtime: {0}", sys.prefix)

                log_config = logging.getLogger("ai.backend.web.config")
                if log_level == LogSeverity.DEBUG:
                    log_config.debug("debug mode enabled.")
                    print("== Web Server configuration ==")
                    pprint(cfg)
                log.info("serving at {0}:{1}", cfg["service"]["ip"], cfg["service"]["port"])
                if cfg["webserver"]["event-loop"] == "uvloop":
                    import uvloop

                    uvloop.install()
                    log.info("Using uvloop as the event loop backend")
                try:
                    aiotools.start_server(
                        server_main_logwrapper,
                        num_workers=min(4, os.cpu_count() or 1),
                        args=(cfg, log_endpoint),
                    )
                finally:
                    log.info("terminated.")
        finally:
            if cfg["webserver"]["pid-file"].is_file():
                # check is_file() to prevent deleting /dev/null!
                cfg["webserver"]["pid-file"].unlink()
    else:
        # Click is going to invoke a subcommand.
        pass


if __name__ == "__main__":
    main()
