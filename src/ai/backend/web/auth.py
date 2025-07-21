import json
from typing import Optional, cast

from aiohttp import web

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession as APISession
from ai.backend.common.clients.http_client.client_pool import ClientKey, ClientPool
from ai.backend.common.web.session import get_session
from ai.backend.web.config.unified import WebServerUnifiedConfig

from . import user_agent


async def get_api_session(
    request: web.Request,
    override_api_endpoint: Optional[str] = None,
) -> APISession:
    config = cast(WebServerUnifiedConfig, request.app["config"])
    api_endpoint = str(config.api.endpoint[0])
    if override_api_endpoint is not None:
        api_endpoint = override_api_endpoint
    session = await get_session(request)
    if not session.get("authenticated", False):
        raise web.HTTPUnauthorized(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/auth-failed",
                "title": "Unauthorized access",
            }),
            content_type="application/problem+json",
        )
    if "token" not in session:
        raise web.HTTPUnauthorized(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/auth-failed",
                "title": "Unauthorized access",
            }),
            content_type="application/problem+json",
        )
    token = session["token"]
    if token["type"] != "keypair":
        raise web.HTTPBadRequest(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/invalid-auth-params",
                "title": "Incompatible auth token type.",
            }),
            content_type="application/problem+json",
        )
    ak, sk = token["access_key"], token["secret_key"]
    client_pool: ClientPool = request.app["client_pool"]
    client_session = client_pool.load_client_session(
        ClientKey(
            endpoint=api_endpoint,
            domain=config.api.domain,
            access_key=ak,
        )
    )
    api_config = APIConfig(
        domain=config.api.domain,
        endpoint=api_endpoint,
        endpoint_type="api",
        access_key=ak,
        secret_key=sk,
        user_agent=user_agent,
        skip_sslcert_validation=not config.api.ssl_verify,
    )
    return APISession(config=api_config, proxy_mode=True, aiohttp_session=client_session)


async def get_anonymous_session(
    request: web.Request,
    override_api_endpoint: Optional[str] = None,
) -> APISession:
    config = cast(WebServerUnifiedConfig, request.app["config"])
    api_endpoint = str(config.api.endpoint[0])
    if override_api_endpoint is not None:
        api_endpoint = override_api_endpoint
    client_pool: ClientPool = request.app["client_pool"]
    client_session = client_pool.load_client_session(
        ClientKey(
            endpoint=api_endpoint,
            domain=config.api.domain,
            access_key="",
        )
    )
    api_config = APIConfig(
        domain=config.api.domain,
        endpoint=api_endpoint,
        endpoint_type="api",
        access_key="",
        secret_key="",
        user_agent=user_agent,
        skip_sslcert_validation=not config.api.ssl_verify,
    )
    return APISession(config=api_config, proxy_mode=True, aiohttp_session=client_session)


def get_client_ip(request: web.Request) -> Optional[str]:
    client_ip = request.headers.get("X-Forwarded-For")
    if not client_ip and request.transport:
        client_ip = request.transport.get_extra_info("peername")[0]
    if not client_ip:
        client_ip = request.remote
    return client_ip


def fill_forwarding_hdrs_to_api_session(
    request: web.Request,
    api_session: APISession,
) -> None:
    _headers = {
        "X-Forwarded-Host": request.headers.get("X-Forwarded-Host", request.host),
        "X-Forwarded-Proto": request.headers.get("X-Forwarded-Proto", request.scheme),
    }
    client_ip = get_client_ip(request)
    if client_ip:
        _headers["X-Forwarded-For"] = client_ip
        api_session.aiohttp_session.headers.update(_headers)
