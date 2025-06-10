from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar, Token
from typing import AsyncGenerator, ClassVar


class ComputeSessionContext:
    _ctxvar: ClassVar[ContextVar[str]] = ContextVar("compute_session_name")

    # TODO: 더 나은 token의 관리 방법?
    _token: ClassVar[dict[str, Token[str]]] = {}

    @classmethod
    def current_session(cls) -> str:
        return cls._ctxvar.get()

    @classmethod
    @actxmgr
    async def with_session(cls, session_name: str) -> AsyncGenerator[None]:
        """
        Context manager to set the compute session for the duration of the context.
        """
        if cls._ctxvar is None:
            raise RuntimeError("ComputeSessionContext is not initialized.")
        cls._token[session_name] = cls._ctxvar.set(session_name)
        try:
            yield
        finally:
            if session_name in cls._token:
                cls._ctxvar.reset(cls._token[session_name])
                del cls._token[session_name]
            else:
                raise RuntimeError(f"No token found for session: {session_name}")
