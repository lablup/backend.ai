from __future__ import annotations

import ipaddress
import json
from typing import Final, cast

from aiohttp import web
from multidict import CIMultiDict

from ai.backend.client.config import APIConfig
from ai.backend.client.session import AsyncSession as APISession
from ai.backend.common.clients.http_client.client_pool import ClientKey, ClientPool
from ai.backend.common.jwt.signer import JWTSigner
from ai.backend.common.jwt.types import JWTUserContext
<<<<<<< HEAD
from ai.backend.common.types import AccessKey
=======
from ai.backend.common.middlewares.request_id import REQUEST_ID_HEADER
from ai.backend.common.types import AccessKey, ReadableCIDR
>>>>>>> 8f2af8dd6 (fix(BA-7374): trust X-Forwarded-For only from configured proxies in the webserver (#17265))
from ai.backend.common.web.session import get_session
from ai.backend.web.clients.endpoint_pool import AcquiredEndpoint
from ai.backend.web.config.unified import WebServerUnifiedConfig

from . import user_agent

TRUSTED_PROXY_NETWORKS_KEY: Final = "_trusted_proxy_networks"


async def get_api_session(
    request: web.Request,
    acquired: AcquiredEndpoint,
) -> APISession:
    config = cast(WebServerUnifiedConfig, request.app["config"])
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
            endpoint=acquired.endpoint,
            domain=config.api.domain,
            access_key=ak,
        )
    )
    api_config = APIConfig(
        domain=config.api.domain,
        endpoint=acquired.endpoint,
        endpoint_type="api",
        access_key=ak,
        secret_key=sk,
        user_agent=user_agent,
        skip_sslcert_validation=not config.api.ssl_verify,
    )
    return APISession(config=api_config, proxy_mode=True, aiohttp_session=client_session)


async def get_anonymous_session(
    request: web.Request,
    acquired: AcquiredEndpoint,
) -> APISession:
    config = cast(WebServerUnifiedConfig, request.app["config"])
    client_pool: ClientPool = request.app["client_pool"]
    client_session = client_pool.load_client_session(
        ClientKey(
            endpoint=acquired.endpoint,
            domain=config.api.domain,
            access_key="",
        )
    )
    api_config = APIConfig(
        domain=config.api.domain,
        endpoint=acquired.endpoint,
        endpoint_type="api",
        access_key="",
        secret_key="",
        user_agent=user_agent,
        skip_sslcert_validation=not config.api.ssl_verify,
    )
    return APISession(config=api_config, proxy_mode=True, aiohttp_session=client_session)


def _forwarded_for_chain(request: web.Request) -> list[str]:
    """Return the client address followed by the proxy hops up to the peer of the connection.

    With trusted proxies configured, entries in front of the first untrusted hop are dropped.
    Without them, every ``X-Forwarded-For`` entry is kept, as the manager does.
    """
    peer = request.remote
    if peer is None:
        return []
    networks: list[ReadableCIDR[ipaddress.IPv4Network | ipaddress.IPv6Network]] = request.app.get(
        TRUSTED_PROXY_NETWORKS_KEY, []
    )
    raw_chain = request.headers.get("X-Forwarded-For", "")
    claimed = [entry.strip() for entry in raw_chain.split(",") if entry.strip()]
    chain = [*claimed, peer]
    if not networks:
        return chain
    for index in reversed(range(len(chain))):
        try:
            address = ipaddress.ip_address(chain[index])
        except ValueError:
            return chain[index:]
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
            address = address.ipv4_mapped
        if not any(
            network.address is not None and address in network.address for network in networks
        ):
            return chain[index:]
    return chain


def get_client_ip(request: web.Request) -> str | None:
    chain = _forwarded_for_chain(request)
    return chain[0] if chain else None


def build_forwarding_headers(request: web.Request) -> CIMultiDict[str]:
    """Build forwarding headers from the incoming request.

    Returns a ``CIMultiDict`` of ``X-Forwarded-*`` HTTP headers that can be
    applied to outgoing requests via ``extra_headers`` parameters or
    :func:`fill_forwarding_hdrs_to_api_session`.
    """
    headers: CIMultiDict[str] = CIMultiDict({
        "X-Forwarded-Host": request.headers.get("X-Forwarded-Host", request.host),
        "X-Forwarded-Proto": request.headers.get("X-Forwarded-Proto", request.scheme),
    })
<<<<<<< HEAD
    client_ip = get_client_ip(request)
    if client_ip:
        headers["X-Forwarded-For"] = client_ip
=======
    chain = _forwarded_for_chain(request)
    if chain:
        headers["X-Forwarded-For"] = ", ".join(chain)
    request_id = current_request_id()
    if request_id is not None:
        headers[REQUEST_ID_HEADER] = request_id
>>>>>>> 8f2af8dd6 (fix(BA-7374): trust X-Forwarded-For only from configured proxies in the webserver (#17265))
    return headers


def fill_forwarding_hdrs_to_api_session(
    request: web.Request,
    api_session: APISession,
) -> None:
    _headers = build_forwarding_headers(request)
    api_session.aiohttp_session.headers.update(_headers)


async def generate_jwt_token_for_session(
    request: web.Request,
) -> str:
    """
    Generate JWT token from current web session.

    Reads user information from the web session and generates a JWT token
    that can be used for authentication with the Backend.AI Manager API.

    Args:
        request: The web request containing the session information

    Returns:
        Generated JWT token string

    Raises:
        web.HTTPUnauthorized: If session is not authenticated or token info is missing
        web.HTTPBadRequest: If token type is incompatible
    """

    config = cast(WebServerUnifiedConfig, request.app["config"])
    session = await get_session(request)

    # Validate session authentication
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

    # Extract user information from session
    access_key = AccessKey(token["access_key"])
    secret_key = token["secret_key"]
    role = session.get("role", "user")

    # Create JWT user context (minimal information)
    # user_id, domain_name, is_admin, is_superadmin will be retrieved from user table during authentication
    user_context = JWTUserContext(
        access_key=access_key,
        role=role,
    )

    # Generate JWT token using user's secret key
    jwt_config = config.jwt.to_jwt_config()
    jwt_signer = JWTSigner(jwt_config)
    return jwt_signer.generate_token(user_context, secret_key)
