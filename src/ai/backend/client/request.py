from __future__ import annotations

import asyncio
import functools
import io
import json as modjson
import logging
import sys
from collections import OrderedDict, namedtuple
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

import aiohttp
import aiohttp.web
import appdirs
import attrs
from aiohttp.client import _RequestContextManager, _WSRequestContextManager
from dateutil.tz import tzutc
from multidict import CIMultiDict
from yarl import URL

from .auth import generate_signature
from .exceptions import BackendAPIError, BackendClientError
from .session import AsyncSession, BaseSession, api_session
from .session import Session as SyncSession

log = logging.getLogger(__spec__.name)

__all__ = [
    "Request",
    "BaseResponse",
    "Response",
    "WebSocketResponse",
    "SSEResponse",
    "FetchContextManager",
    "WebSocketContextManager",
    "SSEContextManager",
    "AttachedFile",
]


RequestContent = Union[
    bytes,
    bytearray,
    str,
    aiohttp.StreamReader,
    io.IOBase,
    None,
]
"""
The type alias for the set of allowed types for request content.
"""


AttachedFile = namedtuple("AttachedFile", "filename stream content_type")
"""
A struct that represents an attached file to the API request.

:param str filename: The name of file to store. It may include paths
                     and the server will create parent directories
                     if required.

:param Any stream: A file-like object that allows stream-reading bytes.

:param str content_type: The content type for the stream.  For arbitrary
                         binary data, use "application/octet-stream".
"""


_T = TypeVar("_T")


async def _coro_return(val: _T) -> _T:
    return val


class ExtendedJSONEncoder(modjson.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class Request:
    """
    The API request object.
    """

    __slots__ = (
        "config",
        "session",
        "method",
        "path",
        "date",
        "headers",
        "params",
        "content_type",
        "api_version",
        "_content",
        "_attached_files",
        "reporthook",
    )

    _content: RequestContent
    _attached_files: Optional[Sequence[AttachedFile]]

    date: Optional[datetime]
    api_version: str

    _allowed_methods = frozenset(["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

    def __init__(
        self,
        method: str = "GET",
        path: str = None,
        content: RequestContent = None,
        *,
        content_type: str = None,
        params: Mapping[str, Union[str, int]] = None,
        reporthook: Callable = None,
        override_api_version: str = None,
    ) -> None:
        """
        Initialize an API request.

        :param BaseSession session: The session where this request is executed on.

        :param str path: The query path. When performing requests, the version number
                         prefix will be automatically prepended if required.

        :param RequestContent content: The API query body which will be encoded as
                                       JSON.

        :param str content_type: Explicitly set the content type.  See also
                                 :func:`Request.set_content`.
        """
        self.session = api_session.get()
        self.config = self.session.config
        self.method = method
        if path is not None and path.startswith("/"):
            path = path[1:]
        self.path = path
        self.params = params
        self.date = None
        if override_api_version:
            self.api_version = override_api_version
        else:
            self.api_version = f"v{self.session.api_version[0]}.{self.session.api_version[1]}"
        self.headers = CIMultiDict([
            ("User-Agent", self.config.user_agent),
            ("X-BackendAI-Domain", self.config.domain),
            ("X-BackendAI-Version", self.api_version),
        ])
        self._content = b""
        self._attached_files = None
        self.set_content(content, content_type=content_type)
        self.reporthook = reporthook

    @property
    def content(self) -> RequestContent:
        """
        Retrieves the content in the original form.
        Private codes should NOT use this as it incurs duplicate
        encoding/decoding.
        """
        return self._content

    def set_content(
        self,
        value: RequestContent,
        *,
        content_type: str = None,
    ) -> None:
        """
        Sets the content of the request.
        """
        assert (
            self._attached_files is None
        ), "cannot set content because you already attached files."
        guessed_content_type = "application/octet-stream"
        if value is None:
            guessed_content_type = "text/plain"
            self._content = b""
        elif isinstance(value, str):
            guessed_content_type = "text/plain"
            self._content = value.encode("utf-8")
        else:
            guessed_content_type = "application/octet-stream"
            self._content = value
        self.content_type = content_type if content_type is not None else guessed_content_type

    def set_json(self, value: Any) -> None:
        """
        A shortcut for set_content() with JSON objects.
        """
        self.set_content(
            modjson.dumps(value, cls=ExtendedJSONEncoder), content_type="application/json"
        )

    def attach_files(self, files: Sequence[AttachedFile]) -> None:
        """
        Attach a list of files represented as AttachedFile.
        """
        assert not self._content, "content must be empty to attach files."
        self.content_type = "multipart/form-data"
        self._attached_files = files

    def _sign(
        self,
        rel_url: URL,
        access_key: str = None,
        secret_key: str = None,
        hash_type: str = None,
    ) -> None:
        """
        Calculates the signature of the given request and adds the
        Authorization HTTP header.
        It should be called at the very end of request preparation and before
        sending the request to the server.
        """
        if access_key is None:
            access_key = self.config.access_key
        if secret_key is None:
            secret_key = self.config.secret_key
        if hash_type is None:
            hash_type = self.config.hash_type
        assert self.date is not None
        if self.config.endpoint_type == "api":
            hdrs, _ = generate_signature(
                method=self.method,
                version=self.api_version,
                endpoint=self.config.endpoint,
                date=self.date,
                rel_url=str(rel_url),
                content_type=self.content_type,
                access_key=access_key,
                secret_key=secret_key,
                hash_type=hash_type,
            )
            self.headers.update(hdrs)
        elif self.config.endpoint_type == "session":
            local_state_path = Path(appdirs.user_state_dir("backend.ai", "Lablup"))
            try:
                cookie_jar = cast(aiohttp.CookieJar, self.session.aiohttp_session.cookie_jar)
                cookie_jar.load(local_state_path / "cookie.dat")
            except (IOError, PermissionError):
                pass
        else:
            raise ValueError("unsupported endpoint type")

    def _pack_content(self) -> Union[RequestContent, aiohttp.FormData]:
        if self._attached_files is not None:
            data = aiohttp.FormData()
            for f in self._attached_files:
                data.add_field("src", f.stream, filename=f.filename, content_type=f.content_type)
            assert data.is_multipart, "Failed to pack files as multipart."
            # Let aiohttp fill up the content-type header including
            # multipart boundaries.
            self.headers.pop("Content-Type", None)
            return data
        else:
            return self._content

    def _build_url(self) -> URL:
        base_url = self.config.endpoint.path.rstrip("/")
        query_path = self.path.lstrip("/") if self.path is not None and len(self.path) > 0 else ""
        if self.config.endpoint_type == "session":
            if not query_path.startswith("server"):
                query_path = "func/{0}".format(query_path)
        path = "{0}/{1}".format(base_url, query_path)
        url = self.config.endpoint.with_path(path)
        if self.params:
            url = url.with_query(self.params)
        return url

    # TODO: attach rate-limit information

    def fetch(self, **kwargs) -> FetchContextManager:
        """
        Sends the request to the server and reads the response.

        You may use this method with AsyncSession only,
        following the pattern below:

        .. code-block:: python3

          from ai.backend.client.request import Request
          from ai.backend.client.session import AsyncSession

          async with AsyncSession() as sess:
            rqst = Request('GET', ...)
            async with rqst.fetch() as resp:
              print(await resp.text())
        """
        assert self.method in self._allowed_methods, "Disallowed HTTP method: {}".format(
            self.method
        )
        self.date = datetime.now(tzutc())
        assert self.date is not None
        self.headers["Date"] = self.date.isoformat()
        if self.content_type is not None and "Content-Type" not in self.headers:
            self.headers["Content-Type"] = self.content_type
        force_anonymous = kwargs.pop("anonymous", False)

        def _rqst_ctx_builder():
            timeout_config = aiohttp.ClientTimeout(
                total=None,
                connect=None,
                sock_connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout,
            )
            full_url = self._build_url()
            if not self.config.is_anonymous and not force_anonymous:
                self._sign(full_url.relative())
            return self.session.aiohttp_session.request(
                self.method,
                str(full_url),
                data=self._pack_content(),
                timeout=timeout_config,
                headers=self.headers,
                allow_redirects=False,
            )

        return FetchContextManager(self.session, _rqst_ctx_builder, **kwargs)

    def connect_websocket(self, **kwargs) -> WebSocketContextManager:
        """
        Creates a WebSocket connection.

        .. warning::

          This method only works with
          :class:`~ai.backend.client.session.AsyncSession`.
        """
        assert isinstance(
            self.session, AsyncSession
        ), "Cannot use websockets with sessions in the synchronous mode"
        assert self.method == "GET", "Invalid websocket method"
        self.date = datetime.now(tzutc())
        assert self.date is not None
        self.headers["Date"] = self.date.isoformat()
        # websocket is always a "binary" stream.
        self.content_type = "application/octet-stream"

        def _ws_ctx_builder():
            full_url = self._build_url()
            if not self.config.is_anonymous:
                self._sign(full_url.relative())
            return self.session.aiohttp_session.ws_connect(
                str(full_url), autoping=True, heartbeat=30.0, headers=self.headers
            )

        return WebSocketContextManager(self.session, _ws_ctx_builder, **kwargs)

    def connect_events(self, **kwargs) -> SSEContextManager:
        """
        Creates a Server-Sent Events connection.

        .. warning::

          This method only works with
          :class:`~ai.backend.client.session.AsyncSession`.
        """
        assert isinstance(
            self.session, AsyncSession
        ), "Cannot use event streams with sessions in the synchronous mode"
        assert self.method == "GET", "Invalid event stream method"
        self.date = datetime.now(tzutc())
        assert self.date is not None
        self.headers["Date"] = self.date.isoformat()
        self.content_type = "application/octet-stream"

        def _rqst_ctx_builder():
            timeout_config = aiohttp.ClientTimeout(
                total=None,
                connect=None,
                sock_connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout,
            )
            full_url = self._build_url()
            if not self.config.is_anonymous:
                self._sign(full_url.relative())
            return self.session.aiohttp_session.request(
                self.method, str(full_url), timeout=timeout_config, headers=self.headers
            )

        return SSEContextManager(self.session, _rqst_ctx_builder, **kwargs)


class AsyncResponseMixin:
    _session: BaseSession
    _raw_response: aiohttp.ClientResponse

    async def text(self) -> str:
        return await self._raw_response.text()

    async def json(self, *, loads=modjson.loads) -> Any:
        loads = functools.partial(loads, object_pairs_hook=OrderedDict)
        return await self._raw_response.json(loads=loads)

    async def read(self, n: int = -1) -> bytes:
        return await self._raw_response.content.read(n)

    async def readall(self) -> bytes:
        return await self._raw_response.content.read(-1)


class SyncResponseMixin:
    _session: BaseSession
    _raw_response: aiohttp.ClientResponse

    def text(self) -> str:
        sync_session = cast(SyncSession, self._session)
        return sync_session.worker_thread.execute(
            self._raw_response.text(),
        )

    def json(self, *, loads=modjson.loads) -> Any:
        loads = functools.partial(loads, object_pairs_hook=OrderedDict)
        sync_session = cast(SyncSession, self._session)
        return sync_session.worker_thread.execute(
            self._raw_response.json(loads=loads),
        )

    def read(self, n: int = -1) -> bytes:
        sync_session = cast(SyncSession, self._session)
        return sync_session.worker_thread.execute(
            self._raw_response.content.read(n),
        )

    def readall(self) -> bytes:
        sync_session = cast(SyncSession, self._session)
        return sync_session.worker_thread.execute(
            self._raw_response.content.read(-1),
        )


class BaseResponse:
    """
    Represents the Backend.AI API response.
    Also serves as a high-level wrapper of :class:`aiohttp.ClientResponse`.

    The response objects are meant to be created by the SDK, not the callers.

    :func:`text`, :func:`json` methods return the resolved content directly with
    plain synchronous Session while they return the coroutines with AsyncSession.
    """

    __slots__ = (
        "_session",
        "_raw_response",
        "_async_mode",
    )

    _session: BaseSession
    _raw_response: aiohttp.ClientResponse
    _async_mode: bool

    def __init__(
        self,
        session: BaseSession,
        underlying_response: aiohttp.ClientResponse,
        *,
        async_mode: bool = False,
        **kwargs,
    ) -> None:
        self._session = session
        self._raw_response = underlying_response
        self._async_mode = async_mode

    @property
    def session(self) -> BaseSession:
        return self._session

    @property
    def status(self) -> int:
        return self._raw_response.status

    @property
    def reason(self) -> str:
        if self._raw_response.reason is not None:
            return self._raw_response.reason
        return ""

    @property
    def headers(self) -> Mapping[str, str]:
        return self._raw_response.headers

    @property
    def raw_response(self) -> aiohttp.ClientResponse:
        return self._raw_response

    @property
    def content_type(self) -> str:
        return self._raw_response.content_type

    @property
    def content_length(self) -> Optional[int]:
        return self._raw_response.content_length

    @property
    def content(self) -> aiohttp.StreamReader:
        return self._raw_response.content


class Response(AsyncResponseMixin, BaseResponse):
    pass


class FetchContextManager:
    """
    The context manager returned by :func:`Request.fetch`.

    It provides asynchronous context manager interfaces only.
    """

    __slots__ = (
        "session",
        "rqst_ctx_builder",
        "response_cls",
        "check_status",
        "_async_mode",
        "_rqst_ctx",
    )

    _rqst_ctx: Optional[_RequestContextManager]

    def __init__(
        self,
        session: BaseSession,
        rqst_ctx_builder: Callable[[], _RequestContextManager],
        *,
        response_cls: Type[Response] = Response,
        check_status: bool = True,
    ) -> None:
        self.session = session
        self.rqst_ctx_builder = rqst_ctx_builder
        self.check_status = check_status
        self.response_cls = response_cls
        self._async_mode = isinstance(session, AsyncSession)
        self._rqst_ctx = None

    async def __aenter__(self) -> Response:
        max_retries = len(self.session.config.endpoints)
        retry_count = 0
        raw_resp: Optional[aiohttp.ClientResponse] = None
        while True:
            try:
                retry_count += 1
                self._rqst_ctx = self.rqst_ctx_builder()
                assert self._rqst_ctx is not None
                raw_resp = await self._rqst_ctx.__aenter__()
                if self.check_status and raw_resp.status // 100 not in [2, 3]:
                    msg = await raw_resp.text()
                    await raw_resp.__aexit__(None, None, None)
                    raise BackendAPIError(raw_resp.status, raw_resp.reason or "", msg)
                return self.response_cls(self.session, raw_resp, async_mode=self._async_mode)
            except aiohttp.ClientConnectionError as e:
                if retry_count == max_retries:
                    msg = (
                        "Request to the API endpoint has failed.\n"
                        "Check your network connection and/or the server status.\n"
                        "\u279c {!r}".format(e)
                    )
                    raise BackendClientError(msg) from e
                else:
                    self.session.config.rotate_endpoints()
                    continue
            except aiohttp.ClientResponseError as e:
                msg = "API endpoint response error.\n\u279c {!r}".format(e)
                if raw_resp is not None:
                    await raw_resp.__aexit__(*sys.exc_info())
                raise BackendClientError(msg) from e
            finally:
                self.session.config.load_balance_endpoints()

    async def __aexit__(self, *exc_info) -> Optional[bool]:
        assert self._rqst_ctx is not None
        await self._rqst_ctx.__aexit__(*exc_info)
        self._rqst_ctx = None
        return None


class WebSocketResponse(BaseResponse):
    """
    A high-level wrapper of :class:`aiohttp.ClientWebSocketResponse`.
    """

    __slots__ = ("_raw_ws",)

    def __init__(
        self,
        session: BaseSession,
        underlying_response: aiohttp.ClientResponse,
        **kwargs,
    ) -> None:
        # Unfortunately, aiohttp.ClientWebSocketResponse is not a subclass of aiohttp.ClientResponse.
        # Since we block methods that require ClientResponse-specific methods, we just force-typecast.
        super().__init__(session, underlying_response, **kwargs)
        self._raw_ws = cast(aiohttp.ClientWebSocketResponse, underlying_response)

    @property
    def content_type(self) -> str:
        raise AttributeError("WebSocketResponse does not have an explicit content type.")

    @property
    def content_length(self) -> Optional[int]:
        raise AttributeError("WebSocketResponse does not have a fixed content length.")

    @property
    def content(self) -> aiohttp.StreamReader:
        raise AttributeError("WebSocketResponse does not support reading the content.")

    @property
    def raw_websocket(self) -> aiohttp.ClientWebSocketResponse:
        return self._raw_ws

    @property
    def closed(self) -> bool:
        return self._raw_ws.closed

    async def close(self) -> None:
        await self._raw_ws.close()

    def __aiter__(self) -> AsyncIterator[aiohttp.WSMessage]:
        return self._raw_ws.__aiter__()

    def exception(self) -> Optional[BaseException]:
        return self._raw_ws.exception()

    async def send_str(self, raw_str: str) -> None:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError("server disconnected")
        await self._raw_ws.send_str(raw_str)

    async def send_json(self, obj: Any) -> None:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError("server disconnected")
        await self._raw_ws.send_json(obj)

    async def send_bytes(self, data: bytes) -> None:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError("server disconnected")
        await self._raw_ws.send_bytes(data)

    async def receive_str(self) -> str:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError("server disconnected")
        return await self._raw_ws.receive_str()

    async def receive_json(self) -> Any:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError("server disconnected")
        return await self._raw_ws.receive_json()

    async def receive_bytes(self) -> bytes:
        if self._raw_ws.closed:
            raise aiohttp.ServerDisconnectedError("server disconnected")
        return await self._raw_ws.receive_bytes()


class WebSocketContextManager:
    """
    The context manager returned by :func:`Request.connect_websocket`.
    """

    __slots__ = (
        "session",
        "ws_ctx_builder",
        "response_cls",
        "on_enter",
        "_ws_ctx",
    )

    _ws_ctx: Optional[_WSRequestContextManager]

    def __init__(
        self,
        session: BaseSession,
        ws_ctx_builder: Callable[[], _WSRequestContextManager],
        *,
        on_enter: Callable = None,
        response_cls: Type[WebSocketResponse] = WebSocketResponse,
    ) -> None:
        self.session = session
        self.ws_ctx_builder = ws_ctx_builder
        self.response_cls = response_cls
        self.on_enter = on_enter
        self._ws_ctx = None

    async def __aenter__(self) -> WebSocketResponse:
        max_retries = len(self.session.config.endpoints)
        retry_count = 0
        while True:
            try:
                retry_count += 1
                self._ws_ctx = self.ws_ctx_builder()
                assert self._ws_ctx is not None
                raw_ws = await self._ws_ctx.__aenter__()
            except aiohttp.ClientConnectionError as e:
                if retry_count == max_retries:
                    msg = (
                        "Request to the API endpoint has failed.\n"
                        "Check your network connection and/or the server status.\n"
                        "Error detail: {!r}".format(e)
                    )
                    raise BackendClientError(msg) from e
                else:
                    self.session.config.rotate_endpoints()
                    continue
            except aiohttp.ClientResponseError as e:
                msg = "API endpoint response error.\n\u279c {!r}".format(e)
                raise BackendClientError(msg) from e
            else:
                break
            finally:
                self.session.config.load_balance_endpoints()

        wrapped_ws = self.response_cls(self.session, cast(aiohttp.ClientResponse, raw_ws))
        if self.on_enter is not None:
            await self.on_enter(wrapped_ws)
        return wrapped_ws

    async def __aexit__(self, *args) -> Optional[bool]:
        assert self._ws_ctx is not None
        await self._ws_ctx.__aexit__(*args)
        self._ws_ctx = None
        return None


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class SSEMessage:
    event: str
    data: str
    id: Optional[str] = None
    retry: Optional[int] = None


class SSEResponse(BaseResponse):
    __slots__ = (
        "_auto_reconnect",
        "_retry",
        "_connector",
    )

    def __init__(
        self,
        session: BaseSession,
        underlying_response: aiohttp.ClientResponse,
        *,
        connector: Callable[[], Awaitable[aiohttp.ClientResponse]],
        auto_reconnect: bool = True,
        default_retry: int = 5,
        **kwargs,
    ) -> None:
        super().__init__(session, underlying_response, async_mode=True, **kwargs)
        self._auto_reconnect = auto_reconnect
        self._retry = default_retry
        self._connector = connector

    async def fetch_events(self) -> AsyncIterator[SSEMessage]:
        msg_lines: List[str] = []
        server_closed = False
        while True:
            received_line = await self._raw_response.content.readline()
            if not received_line:
                # connection closed
                if self._auto_reconnect and not server_closed:
                    await asyncio.sleep(self._retry)
                    self._raw_response = await self._connector()
                    continue
                else:
                    break
            received_line = received_line.strip(b"\r\n")
            if received_line.startswith(b":"):
                # comment
                continue
            if not received_line:
                # message boundary
                if len(msg_lines) == 0:
                    continue
                event_type = "message"
                event_id = None
                event_retry = None
                data_lines = []
                try:
                    for stored_line in msg_lines:
                        hdr, text = stored_line.split(":", maxsplit=1)
                        text = text.lstrip(" ")
                        if hdr == "data":
                            data_lines.append(text)
                        elif hdr == "event":
                            event_type = text
                        elif hdr == "id":
                            event_id = text
                        elif hdr == "retry":
                            event_retry = int(text)
                except (IndexError, ValueError):
                    log.exception("SSEResponse: parsing-error")
                    continue
                event_data = "\n".join(data_lines)
                msg_lines.clear()
                if event_retry is not None:
                    self._retry = event_retry
                yield SSEMessage(
                    event=event_type,
                    data=event_data,
                    id=event_id,
                    retry=event_retry,
                )
                if event_type == "server_close":
                    server_closed = True
                    break
            else:
                msg_lines.append(received_line.decode("utf-8"))

    def __aiter__(self) -> AsyncIterator[SSEMessage]:
        return self.fetch_events()


class SSEContextManager:
    __slots__ = (
        "session",
        "rqst_ctx_builder",
        "response_cls",
        "_rqst_ctx",
    )

    _rqst_ctx: Optional[_RequestContextManager]

    def __init__(
        self,
        session: BaseSession,
        rqst_ctx_builder: Callable[[], _RequestContextManager],
        *,
        response_cls: Type[SSEResponse] = SSEResponse,
    ) -> None:
        self.session = session
        self.rqst_ctx_builder = rqst_ctx_builder
        self.response_cls = response_cls
        self._rqst_ctx = None

    async def reconnect(self) -> aiohttp.ClientResponse:
        if self._rqst_ctx is not None:
            await self._rqst_ctx.__aexit__(None, None, None)
        self._rqst_ctx = self.rqst_ctx_builder()
        assert self._rqst_ctx is not None
        raw_resp = await self._rqst_ctx.__aenter__()
        if raw_resp.status // 100 != 2:
            msg = await raw_resp.text()
            raise BackendAPIError(raw_resp.status, raw_resp.reason or "", msg)
        return raw_resp

    async def __aenter__(self) -> SSEResponse:
        max_retries = len(self.session.config.endpoints)
        retry_count = 0
        while True:
            try:
                retry_count += 1
                raw_resp = await self.reconnect()
                return self.response_cls(self.session, raw_resp, connector=self.reconnect)
            except aiohttp.ClientConnectionError as e:
                if retry_count == max_retries:
                    msg = (
                        "Request to the API endpoint has failed.\n"
                        "Check your network connection and/or the server status.\n"
                        "\u279c {!r}".format(e)
                    )
                    raise BackendClientError(msg) from e
                else:
                    self.session.config.rotate_endpoints()
                    continue
            except aiohttp.ClientResponseError as e:
                msg = "API endpoint response error.\n\u279c {!r}".format(e)
                raise BackendClientError(msg) from e
            finally:
                self.session.config.load_balance_endpoints()

    async def __aexit__(self, *args) -> Optional[bool]:
        assert self._rqst_ctx is not None
        await self._rqst_ctx.__aexit__(*args)
        self._rqst_ctx = None
        return None
