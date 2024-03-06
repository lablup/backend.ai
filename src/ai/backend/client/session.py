from __future__ import annotations

import abc
import asyncio
import inspect
import queue
import threading
import warnings
from contextvars import Context, ContextVar, copy_context
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Coroutine,
    Iterator,
    Literal,
    Tuple,
    TypeVar,
    Union,
)

import aiohttp
from multidict import CIMultiDict

from .config import MIN_API_VERSION, APIConfig, get_config, parse_api_version
from .exceptions import APIVersionWarning, BackendAPIError, BackendClientError
from .types import Sentinel, sentinel

__all__ = (
    "BaseSession",
    "Session",
    "AsyncSession",
    "api_session",
)

from ..common.types import SSLContextType

api_session: ContextVar[BaseSession] = ContextVar("api_session")


async def _negotiate_api_version(
    http_session: aiohttp.ClientSession,
    config: APIConfig,
) -> Tuple[int, str]:
    client_version = parse_api_version(config.version)
    try:
        timeout_config = aiohttp.ClientTimeout(
            total=None,
            connect=None,
            sock_connect=config.connection_timeout,
            sock_read=config.read_timeout,
        )
        headers = CIMultiDict([
            ("User-Agent", config.user_agent),
        ])
        probe_url = (
            config.endpoint / "func/" if config.endpoint_type == "session" else config.endpoint
        )
        async with http_session.get(probe_url, timeout=timeout_config, headers=headers) as resp:
            resp.raise_for_status()
            server_info = await resp.json()
            server_version = parse_api_version(server_info["version"])
            if server_version > client_version:
                warnings.warn(
                    "The server API version is higher than the client. "
                    "Please upgrade the client package.",
                    category=APIVersionWarning,
                )
            if server_version < MIN_API_VERSION:
                warnings.warn(
                    f"The server is too old ({server_version}) and does not meet the minimum API version"
                    f" requirement: v{MIN_API_VERSION[0]}.{MIN_API_VERSION[1]}\nPlease upgrade"
                    " the server or downgrade/reinstall the client SDK with the same"
                    " major.minor release of the server.",
                    category=APIVersionWarning,
                )
            return min(server_version, client_version)
    except (asyncio.TimeoutError, aiohttp.ClientError):
        # fallback to the configured API version
        return client_version


async def _close_aiohttp_session(session: aiohttp.ClientSession) -> None:
    # This is a hacky workaround for premature closing of SSL transports
    # on Windows Proactor event loops.
    # Thanks to Vadim Markovtsev's comment on the aiohttp issue #1925.
    # (https://github.com/aio-libs/aiohttp/issues/1925#issuecomment-592596034)
    transports = 0
    all_is_lost = asyncio.Event()
    if session.connector is None:
        all_is_lost.set()
    else:
        if len(session.connector._conns) == 0:
            all_is_lost.set()
        for conn in session.connector._conns.values():
            for handler, _ in conn:
                proto = getattr(handler.transport, "_ssl_protocol", None)
                if proto is None:
                    continue
                transports += 1
                orig_lost = proto.connection_lost
                orig_eof_received = proto.eof_received

                def connection_lost(exc):
                    orig_lost(exc)
                    nonlocal transports
                    transports -= 1
                    if transports == 0:
                        all_is_lost.set()

                def eof_received():
                    try:
                        orig_eof_received()
                    except AttributeError:
                        # It may happen that eof_received() is called after
                        # _app_protocol and _transport are set to None.
                        pass

                proto.connection_lost = connection_lost
                proto.eof_received = eof_received
    await session.close()
    if transports > 0:
        await all_is_lost.wait()


_Item = TypeVar("_Item")


class _SyncWorkerThread(threading.Thread):
    work_queue: queue.Queue[
        Union[
            Tuple[Union[AsyncIterator, Coroutine], Context],
            Sentinel,
        ]
    ]
    done_queue: queue.Queue[Union[Any, Exception]]
    stream_queue: queue.Queue[Union[Any, Exception, Sentinel]]
    stream_block: threading.Event
    agen_shutdown: bool

    __slots__ = (
        "work_queue",
        "done_queue",
        "stream_queue",
        "stream_block",
        "agen_shutdown",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.work_queue = queue.Queue()
        self.done_queue = queue.Queue()
        self.stream_queue = queue.Queue()
        self.stream_block = threading.Event()
        self.agen_shutdown = False

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            while True:
                item = self.work_queue.get()
                if item is sentinel:
                    break
                coro, ctx = item
                if inspect.isasyncgen(coro):
                    ctx.run(loop.run_until_complete, self.agen_wrapper(coro))
                else:
                    try:
                        # FIXME: Once python/mypy#12756 is resolved, remove the type-ignore tag.
                        result = ctx.run(loop.run_until_complete, coro)  # type: ignore
                    except Exception as e:
                        self.done_queue.put_nowait(e)
                    else:
                        self.done_queue.put_nowait(result)
                self.work_queue.task_done()
        except (SystemExit, KeyboardInterrupt):
            pass
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.stop()
            loop.close()

    def execute(self, coro: Coroutine) -> Any:
        ctx = copy_context()  # preserve context for the worker thread
        try:
            self.work_queue.put((coro, ctx))
            result = self.done_queue.get()
            self.done_queue.task_done()
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            del ctx

    async def agen_wrapper(self, agen):
        self.agen_shutdown = False
        try:
            async for item in agen:
                self.stream_block.clear()
                self.stream_queue.put(item)
                # flow-control the generator.
                self.stream_block.wait()
                if self.agen_shutdown:
                    break
        except Exception as e:
            self.stream_queue.put(e)
        finally:
            self.stream_queue.put(sentinel)
            await agen.aclose()

    def execute_generator(self, asyncgen: AsyncIterator[_Item]) -> Iterator[_Item]:
        ctx = copy_context()  # preserve context for the worker thread
        try:
            self.work_queue.put((asyncgen, ctx))
            while True:
                item = self.stream_queue.get()
                try:
                    if item is sentinel:
                        break
                    if isinstance(item, Exception):
                        raise item
                    yield item
                finally:
                    self.stream_block.set()
                    self.stream_queue.task_done()
        finally:
            del ctx

    def interrupt_generator(self):
        self.agen_shutdown = True
        self.stream_block.set()
        self.stream_queue.put(sentinel)


class BaseSession(metaclass=abc.ABCMeta):
    """
    The base abstract class for sessions.
    """

    __slots__ = (
        "_config",
        "_closed",
        "_context_token",
        "_proxy_mode",
        "aiohttp_session",
        "api_version",
        "System",
        "Manager",
        "Admin",
        "Agent",
        "AgentWatcher",
        "ScalingGroup",
        "Storage",
        "Image",
        "ComputeSession",
        "SessionTemplate",
        "Domain",
        "Group",
        "Auth",
        "User",
        "KeyPair",
        "BackgroundTask",
        "EtcdConfig",
        "Resource",
        "KeypairResourcePolicy",
        "VFolder",
        "Dotfile",
        "ServerLog",
        "Permission",
        "Service",
        "Model",
        "QuotaScope",
    )

    aiohttp_session: aiohttp.ClientSession
    api_version: Tuple[int, str]

    _closed: bool
    _config: APIConfig
    _proxy_mode: bool

    def __init__(
        self,
        *,
        config: APIConfig = None,
        proxy_mode: bool = False,
    ) -> None:
        self._closed = False
        self._config = config if config else get_config()
        self._proxy_mode = proxy_mode
        self.api_version = parse_api_version(self._config.version)

        from .func.acl import Permission
        from .func.admin import Admin
        from .func.agent import Agent, AgentWatcher
        from .func.auth import Auth
        from .func.bgtask import BackgroundTask
        from .func.domain import Domain
        from .func.dotfile import Dotfile
        from .func.etcd import EtcdConfig
        from .func.group import Group
        from .func.image import Image
        from .func.keypair import KeyPair
        from .func.keypair_resource_policy import KeypairResourcePolicy
        from .func.manager import Manager
        from .func.model import Model
        from .func.quota_scope import QuotaScope
        from .func.resource import Resource
        from .func.scaling_group import ScalingGroup
        from .func.server_log import ServerLog
        from .func.service import Service
        from .func.session import ComputeSession
        from .func.session_template import SessionTemplate
        from .func.storage import Storage
        from .func.system import System
        from .func.user import User
        from .func.vfolder import VFolder

        self.System = System
        self.Admin = Admin
        self.Agent = Agent
        self.AgentWatcher = AgentWatcher
        self.Storage = Storage
        self.Auth = Auth
        self.BackgroundTask = BackgroundTask
        self.EtcdConfig = EtcdConfig
        self.Domain = Domain
        self.Group = Group
        self.Image = Image
        self.ComputeSession = ComputeSession
        self.KeyPair = KeyPair
        self.Manager = Manager
        self.Resource = Resource
        self.KeypairResourcePolicy = KeypairResourcePolicy
        self.User = User
        self.ScalingGroup = ScalingGroup
        self.SessionTemplate = SessionTemplate
        self.VFolder = VFolder
        self.Dotfile = Dotfile
        self.ServerLog = ServerLog
        self.Permission = Permission
        self.Service = Service
        self.Model = Model
        self.QuotaScope = QuotaScope

    @property
    def proxy_mode(self) -> bool:
        """
        If set True, it skips API version negotiation when opening the session.
        """
        return self._proxy_mode

    @abc.abstractmethod
    def open(self) -> Union[None, Awaitable[None]]:
        """
        Initializes the session and perform version negotiation.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> Union[None, Awaitable[None]]:
        """
        Terminates the session and releases underlying resources.
        """
        raise NotImplementedError

    @property
    def closed(self) -> bool:
        """
        Checks if the session is closed.
        """
        return self._closed

    @property
    def config(self) -> APIConfig:
        """
        The configuration used by this session object.
        """
        return self._config

    def __enter__(self) -> BaseSession:
        raise NotImplementedError

    def __exit__(self, *exc_info) -> Literal[False]:
        return False

    async def __aenter__(self) -> BaseSession:
        raise NotImplementedError

    async def __aexit__(self, *exc_info) -> Literal[False]:
        return False


class Session(BaseSession):
    """
    A context manager for API client sessions that makes API requests synchronously.
    You may call simple request-response APIs like a plain Python function,
    but cannot use streaming APIs based on WebSocket and Server-Sent Events.
    """

    __slots__ = ("_worker_thread",)

    def __init__(
        self,
        *,
        config: APIConfig = None,
        proxy_mode: bool = False,
    ) -> None:
        super().__init__(config=config, proxy_mode=proxy_mode)
        self._worker_thread = _SyncWorkerThread()
        self._worker_thread.start()

        async def _create_aiohttp_session() -> aiohttp.ClientSession:
            ssl: SSLContextType = True
            if self._config.skip_sslcert_validation:
                ssl = False
            connector = aiohttp.TCPConnector(ssl=ssl)
            return aiohttp.ClientSession(connector=connector)

        self.aiohttp_session = self.worker_thread.execute(_create_aiohttp_session())

    def open(self) -> None:
        self._context_token = api_session.set(self)
        if not self._proxy_mode:
            self.api_version = self.worker_thread.execute(
                _negotiate_api_version(self.aiohttp_session, self.config)
            )

    def close(self) -> None:
        """
        Terminates the session.  It schedules the ``close()`` coroutine
        of the underlying aiohttp session and then enqueues a sentinel
        object to indicate termination.  Then it waits until the worker
        thread to self-terminate by joining.
        """
        if self._closed:
            return
        self._closed = True
        self._worker_thread.interrupt_generator()
        self._worker_thread.execute(_close_aiohttp_session(self.aiohttp_session))
        self._worker_thread.work_queue.put(sentinel)
        self._worker_thread.join()
        api_session.reset(self._context_token)

    @property
    def worker_thread(self):
        """
        The thread that internally executes the asynchronous implementations
        of the given API functions.
        """
        return self._worker_thread

    def __enter__(self) -> Session:
        assert not self.closed, "Cannot reuse closed session"
        self.open()
        if self.config.announcement_handler:
            try:
                payload = self.Manager.get_announcement()
                if payload["enabled"]:
                    self.config.announcement_handler(payload["message"])
            except (BackendClientError, BackendAPIError):
                # The server may be an old one without announcement API.
                pass
        return self

    def __exit__(self, *exc_info) -> Literal[False]:
        self.close()
        return False  # raise up the inner exception


class AsyncSession(BaseSession):
    """
    A context manager for API client sessions that makes API requests asynchronously.
    You may call all APIs as coroutines.
    WebSocket-based APIs and SSE-based APIs returns special response types.
    """

    def __init__(
        self,
        *,
        config: APIConfig = None,
        proxy_mode: bool = False,
    ) -> None:
        super().__init__(config=config, proxy_mode=proxy_mode)
        ssl: SSLContextType = True
        if self._config.skip_sslcert_validation:
            ssl = False
        connector = aiohttp.TCPConnector(ssl=ssl)
        self.aiohttp_session = aiohttp.ClientSession(connector=connector)

    async def _aopen(self) -> None:
        self._context_token = api_session.set(self)
        if not self._proxy_mode:
            self.api_version = await _negotiate_api_version(self.aiohttp_session, self.config)

    def open(self) -> Awaitable[None]:
        return self._aopen()

    async def _aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        await _close_aiohttp_session(self.aiohttp_session)
        api_session.reset(self._context_token)

    def close(self) -> Awaitable[None]:
        return self._aclose()

    async def __aenter__(self) -> AsyncSession:
        assert not self.closed, "Cannot reuse closed session"
        await self.open()
        if self.config.announcement_handler:
            try:
                payload = await self.Manager.get_announcement()
                if payload["enabled"]:
                    self.config.announcement_handler(payload["message"])
            except (BackendClientError, BackendAPIError):
                # The server may be an old one without announcement API.
                pass
        return self

    async def __aexit__(self, *exc_info) -> Literal[False]:
        await self.close()
        return False  # raise up the inner exception
