from __future__ import annotations

import json
import logging
import logging.config
import uuid
from typing import Any, Callable, Optional

import redis
import redis.asyncio as aioredis
from aiohttp import web

from ai.backend.common.logging import BraceStyleAdapter

from . import AbstractStorage, Session, extra_config_headers

log = BraceStyleAdapter(logging.getLogger("ai.backend.web.server"))


class RedisStorage(AbstractStorage):
    """Redis storage"""

    def __init__(
        self,
        redis_pool: aioredis.Redis,
        *,
        cookie_name: str = "AIOHTTP_SESSION",
        domain: Optional[str] = None,
        max_age: Optional[int] = None,
        path: str = "/",
        secure: Optional[bool] = None,
        httponly: bool = True,
        samesite: Optional[str] = None,
        key_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
        encoder: Callable[[object], str] = json.dumps,
        decoder: Callable[[str], Any] = json.loads,
    ) -> None:
        super().__init__(
            cookie_name=cookie_name,
            domain=domain,
            max_age=max_age,
            path=path,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
            encoder=encoder,
            decoder=decoder,
        )
        if aioredis is None:
            raise RuntimeError("Please install redis")
        # May have installed aioredis separately (without aiohttp-session[aioredis]).
        lib_version = redis.VERSION[:2]
        if lib_version < (4, 3):
            raise RuntimeError("redis<4.3 is not supported")
        self._key_factory = key_factory
        if not isinstance(redis_pool, aioredis.Redis):
            raise TypeError(f"Expected redis.asyncio.Redis got {type(redis_pool)}")
        self._redis = redis_pool

    async def load_session(self, request: web.Request) -> Session:
        # If X-BackendAI-SessionID exists in request, login will use the value as SessionID,
        # instead of Cookie value.
        request_headers = extra_config_headers.check(request.headers)
        sessionId = request_headers.get("X-BackendAI-SessionID", None)
        if sessionId is not None:
            key = str(sessionId)
        else:
            cookie = self.load_cookie(request)
            if cookie is None:
                return Session(None, data=None, new=True, max_age=self.max_age)
            else:
                key = str(cookie)
        data_bytes = await self._redis.get(self.cookie_name + "_" + key)
        if data_bytes is None:
            return Session(None, data=None, new=True, max_age=self.max_age)
        try:
            data = self._decoder(data_bytes)
        except ValueError:
            data = None
        return Session(key, data=data, new=False, max_age=self.max_age)

    async def save_session(
        self, request: web.Request, response: web.StreamResponse, session: Session
    ) -> None:
        key = session.identity
        if key is None:
            # New login case
            key = self._key_factory()
            response._headers["X-BackendAI-SessionID"] = key
            # session.set_new_identity(key)
            self.save_cookie(response, key, max_age=session.max_age)
        else:
            if session.empty:
                # Logout or refresh
                self.save_cookie(response, "", max_age=session.max_age)
                # response.headers.set('X-BackendAI-SessionID', "")
            else:
                key = str(key)
                self.save_cookie(response, key, max_age=session.max_age)
                # response.headers.set('X-BackendAI-SessionID', key)

        data_str = self._encoder(self._get_session_data(session))
        await self._redis.set(
            self.cookie_name + "_" + key,
            data_str,
            ex=session.max_age,
        )
