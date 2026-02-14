from __future__ import annotations

import ssl
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import aiohttp

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel

from .auth import AuthStrategy
from .config import ClientConfig
from .exceptions import map_status_to_exception


class BackendAIClient:
    """Async HTTP client for Backend.AI REST API.

    All public request methods accept and return Pydantic models only.
    Use ``typed_request()`` as the sole public interface for making API calls.

    Prefer ``create()`` for production use; ``__init__`` accepts a pre-built
    session so tests can inject a mock directly.
    """

    _config: ClientConfig
    _auth: AuthStrategy
    _session: aiohttp.ClientSession

    def __init__(
        self,
        config: ClientConfig,
        auth: AuthStrategy,
        session: aiohttp.ClientSession,
    ) -> None:
        self._config = config
        self._auth = auth
        self._session = session

    @classmethod
    async def create(
        cls,
        config: ClientConfig,
        auth: AuthStrategy,
    ) -> BackendAIClient:
        ssl_context: ssl.SSLContext | bool = not config.skip_ssl_verification
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(
            sock_connect=config.connection_timeout or None,
            sock_read=config.read_timeout or None,
        )
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        )
        return cls(config, auth, session)

    async def close(self) -> None:
        await self._session.close()

    def _build_url(self, path: str) -> str:
        base = str(self._config.endpoint).rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def _sign(self, method: str, rel_url: str, content_type: str) -> Mapping[str, str]:
        now = datetime.now(UTC)
        headers = self._auth.sign(
            method=method,
            version=self._config.api_version,
            endpoint=self._config.endpoint,
            date=now,
            rel_url=rel_url,
            content_type=content_type,
        )
        return {
            "Date": now.isoformat(),
            "Content-Type": content_type,
            "X-BackendAI-Version": self._config.api_version,
            **headers,
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        session = self._session
        content_type = "application/json"
        rel_url = "/" + path.lstrip("/")
        headers = self._sign(method, rel_url, content_type)
        url = self._build_url(path)
        async with session.request(
            method,
            url,
            headers=headers,
            json=json,
            params=params,
        ) as resp:
            if resp.status >= 400:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", data)
            result: dict[str, Any] = await resp.json()
            return result

    async def typed_request[T: BaseResponseModel](
        self,
        method: str,
        path: str,
        *,
        request: BaseRequestModel | None = None,
        response_model: type[T],
        params: dict[str, str] | None = None,
    ) -> T:
        json_body = request.model_dump(exclude_none=True) if request is not None else None
        data = await self._request(method, path, json=json_body, params=params)
        return response_model.model_validate(data)

    async def fire_and_forget(
        self,
        method: str,
        path: str,
        *,
        request: BaseRequestModel | None = None,
        params: dict[str, str] | None = None,
    ) -> None:
        """Send a request and discard the response body.

        Use this for endpoints that return ``204 No Content`` or similar
        status codes with no JSON body.
        """
        json_body = request.model_dump(exclude_none=True) if request is not None else None
        session = self._session
        content_type = "application/json"
        rel_url = "/" + path.lstrip("/")
        headers = self._sign(method, rel_url, content_type)
        url = self._build_url(path)
        async with session.request(
            method,
            url,
            headers=headers,
            json=json_body,
            params=params,
        ) as resp:
            if resp.status >= 400:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", data)
