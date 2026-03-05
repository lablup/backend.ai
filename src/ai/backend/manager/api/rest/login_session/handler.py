"""Login session handler.

Provides stub endpoints for login session management.
All methods raise NotImplementedAPI until the integration story (BA-4905) is completed.
"""

from __future__ import annotations

import logging
from typing import Final

from ai.backend.common.api_handlers import APIResponse, PathParam
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.dto.login_session_request import RevokeLoginSessionPathParam
from ai.backend.manager.errors.api import NotImplementedAPI

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LoginSessionHandler:
    """Login session API handler with constructor-injected dependencies."""

    # ------------------------------------------------------------------
    # list_sessions (GET /login-sessions)
    # ------------------------------------------------------------------

    async def list_sessions(self, ctx: UserContext) -> APIResponse:
        log.info("LOGIN_SESSION.LIST(ak:{})", ctx.access_key)
        raise NotImplementedAPI

    # ------------------------------------------------------------------
    # revoke_session (DELETE /login-sessions/{session_id})
    # ------------------------------------------------------------------

    async def revoke_session(
        self,
        path: PathParam[RevokeLoginSessionPathParam],
        ctx: UserContext,
    ) -> APIResponse:
        params = path.parsed
        log.info("LOGIN_SESSION.REVOKE(ak:{}, session_id:{})", ctx.access_key, params.session_id)
        raise NotImplementedAPI
