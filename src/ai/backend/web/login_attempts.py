from __future__ import annotations

import json
import logging
from typing import Final, cast

from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.logging.structured import StructuredLogger
from ai.backend.web.auth import get_client_ip
from ai.backend.web.config.unified import WebServerUnifiedConfig

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


async def reserve_login_attempt(request: web.Request, username: str) -> None:
    """Count an attempt against the user, or raise 429 if the user is blocked.

    Reserving before the password check keeps concurrent attempts within the limit.
    """
    config = cast(WebServerUnifiedConfig, request.app["config"])
    valkey_client = cast(ValkeySessionClient, request.app["redis"])
    if await valkey_client.reserve_login_attempt(
        username,
        config.session.login_allowed_fail_count,
        config.session.login_block_time,
    ):
        return
    log.trace(
        "login blocked after consecutive failures",
        user_email=username,
        client_ip=get_client_ip(request),
    )
    raise web.HTTPTooManyRequests(
        text=json.dumps({
            "type": "https://api.backend.ai/probs/too-many-requests",
            "title": "Too many failed login attempts",
        }),
        content_type="application/problem+json",
    )
