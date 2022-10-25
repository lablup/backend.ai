import json
import uuid
from typing import Any, Callable, Optional

from aiohttp import web

from . import AbstractStorage, Session

try:
    from redis import VERSION
    from redis import asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]


class RedisStorage(AbstractStorage):
    """Redis storage"""

    def __init__(
        self,
        redis_pool: "aioredis.Redis[bytes]",
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
        lib_version = VERSION[:2]
        if lib_version < (4, 3):
            raise RuntimeError("redis<4.3 is not supported")
        self._key_factory = key_factory
        if not isinstance(redis_pool, aioredis.Redis):
            raise TypeError(f"Expected redis.asyncio.Redis got {type(redis_pool)}")
        self._redis = redis_pool

    async def load_session(self, request: web.Request) -> Session:
        cookie = self.load_cookie(request)
        if cookie is None:
            return Session(None, data=None, new=True, max_age=self.max_age)
        else:
            key = str(cookie)
            data_bytes = await self._redis.get(self.cookie_name + "_" + key)
            if data_bytes is None:
                return Session(None, data=None, new=True, max_age=self.max_age)
            data_str = data_bytes.decode("utf-8")
            try:
                data = self._decoder(data_str)
            except ValueError:
                data = None
            return Session(key, data=data, new=False, max_age=self.max_age)

    async def save_session(
        self, request: web.Request, response: web.StreamResponse, session: Session
    ) -> None:
        key = session.identity
        if key is None:
            key = self._key_factory()
            self.save_cookie(response, key, max_age=session.max_age)
        else:
            if session.empty:
                self.save_cookie(response, "", max_age=session.max_age)
            else:
                key = str(key)
                self.save_cookie(response, key, max_age=session.max_age)

        data_str = self._encoder(self._get_session_data(session))
        await self._redis.set(
            self.cookie_name + "_" + key,
            data_str,
            ex=session.max_age,
        )
