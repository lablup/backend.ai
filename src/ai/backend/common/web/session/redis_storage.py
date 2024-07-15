from __future__ import annotations

import json
import logging
import logging.config
import uuid
from typing import Any, Callable, Optional

import redis
import redis.asyncio as aioredis
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter

from . import AbstractStorage, Session, extra_config_headers

log = BraceStyleAdapter(logging.getLogger("ai.backend.web.server"))


class RedisStorage(AbstractStorage):
    """Redis storage"""

    @property
    def login_session_extend_time(self) -> Optional[int]:
        return self._login_session_extend_time

    def __init__(
        self,
        redis_pool: aioredis.Redis,
        *,
        cookie_name: str = "AIOHTTP_SESSION",
        domain: Optional[str] = None,
        max_age: Optional[int] = None,
        login_session_extend_time: Optional[int] = None,
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
        self._login_session_extend_time = login_session_extend_time

    async def get_redis_time(self) -> int:
        server_time = await self._redis.time()
        return int(server_time[0])

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
                return Session(
                    None, data=None, new=True, expires=self.expires
                )  # max_age=self.max_age
            else:
                key = str(cookie)
        data_bytes = await self._redis.get(self.cookie_name + "_" + key)
        if data_bytes is None:
            return Session(None, data=None, new=True, expires=self.expires)  # max_age=self.max_age
        try:
            data = self._decoder(data_bytes)
        except ValueError:
            data = None
        return Session(key, data=data, new=False, expires=self.expires)

    async def update_expires(self, session: Session) -> None:
        redis_time: int = await self.get_redis_time()
        expires_time = redis_time
        if self.expires is None or self.login_session_extend_time is None:
            if session.max_age is not None:
                expires_time += int(session.max_age)
            self.expires = expires_time
        else:
            expires_time += self.login_session_extend_time
            self.expires = expires_time

    async def save_session(
        self, request: web.Request, response: web.StreamResponse, session: Session
    ) -> None:
        key = session.identity
        await self.update_expires(session)
        if key is None:
            # New login case
            key = self._key_factory()
            response._headers["X-BackendAI-SessionID"] = key
            # session.set_new_identity(key)
            self.save_cookie(
                response=response, cookie_data=key, expires=self.expires, max_age=self.max_age
            )
        else:
            if session.empty:
                # Logout or refresh
                self.save_cookie(
                    response=response,
                    cookie_data="",
                    expires=self.expires,
                    max_age=self.max_age
                    if self.login_session_extend_time is None
                    else self.login_session_extend_time,
                )
                # response.headers.set('X-BackendAI-SessionID', "")
            else:
                key = str(key)
                self.save_cookie(
                    response=response,
                    cookie_data=key,
                    expires=self.expires,
                    max_age=self.max_age
                    if self.login_session_extend_time is None
                    else self.login_session_extend_time,
                )
                # response.headers.set('X-BackendAI-SessionID', key)

        data_str = self._encoder(self._get_session_data(session))
        await self._redis.set(
            name=self.cookie_name + "_" + key,
            value=data_str,
            ex=self.max_age if self.expires is None else self.login_session_extend_time,
        )
