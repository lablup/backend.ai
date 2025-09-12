from __future__ import annotations

import abc
import asyncio
import warnings
from contextvars import ContextVar
from typing import (
    Awaitable,
    Literal,
    Optional,
    Tuple,
    Union,
)

import aiohttp
from multidict import CIMultiDict

from ai.backend.common.sync import SyncWorkerThread
from ai.backend.common.types import Sentinel

from .config import MIN_API_VERSION, APIConfig, get_config, parse_api_version
from .exceptions import APIVersionWarning, BackendAPIError, BackendClientError

__all__ = (
    "BaseSession",
    "Session",
    "AsyncSession",
    "api_session",
)

from contextlib import asynccontextmanager as actxmgr

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
        "ContainerRegistry",
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
        "ServiceAutoScalingRule",
        "Model",
        "QuotaScope",
        "Network",
        "UserResourcePolicy",
    )

    aiohttp_session: aiohttp.ClientSession
    api_version: Tuple[int, str]

    _closed: bool
    _config: APIConfig
    _proxy_mode: bool

    def __init__(
        self,
        *,
        config: Optional[APIConfig] = None,
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
        from .func.container_registry import ContainerRegistry
        from .func.domain import Domain
        from .func.dotfile import Dotfile
        from .func.etcd import EtcdConfig
        from .func.group import Group
        from .func.image import Image
        from .func.keypair import KeyPair
        from .func.keypair_resource_policy import KeypairResourcePolicy
        from .func.manager import Manager
        from .func.model import Model
        from .func.network import Network
        from .func.quota_scope import QuotaScope
        from .func.resource import Resource
        from .func.scaling_group import ScalingGroup
        from .func.server_log import ServerLog
        from .func.service import Service
        from .func.service_auto_scaling_rule import ServiceAutoScalingRule
        from .func.session import ComputeSession
        from .func.session_template import SessionTemplate
        from .func.storage import Storage
        from .func.system import System
        from .func.user import User
        from .func.user_resource_policy import UserResourcePolicy
        from .func.vfolder import VFolderByName

        self.System = System
        self.Admin = Admin
        self.Agent = Agent
        self.AgentWatcher = AgentWatcher
        self.Storage = Storage
        self.Auth = Auth
        self.BackgroundTask = BackgroundTask
        self.ContainerRegistry = ContainerRegistry
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
        self.VFolder = VFolderByName
        self.Dotfile = Dotfile
        self.ServerLog = ServerLog
        self.Permission = Permission
        self.Service = Service
        self.ServiceAutoScalingRule = ServiceAutoScalingRule
        self.Model = Model
        self.QuotaScope = QuotaScope
        self.Network = Network
        self.UserResourcePolicy = UserResourcePolicy

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

    __slots__ = ("_owns_session", "_worker_thread")

    def __init__(
        self,
        *,
        config: Optional[APIConfig] = None,
        proxy_mode: bool = False,
        aiohttp_session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        super().__init__(config=config, proxy_mode=proxy_mode)
        self._worker_thread = SyncWorkerThread()
        self._worker_thread.start()

        if aiohttp_session is not None:
            self.aiohttp_session = aiohttp_session
            self._owns_session = False
        else:

            async def _create_aiohttp_session() -> aiohttp.ClientSession:
                return _default_http_client_session(self._config.skip_sslcert_validation)

            self.aiohttp_session = self.worker_thread.execute(_create_aiohttp_session())
            self._owns_session = True

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
        if self._owns_session:
            self._worker_thread.execute(_close_aiohttp_session(self.aiohttp_session))
        self._worker_thread.work_queue.put(Sentinel.TOKEN)
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


def _default_http_client_session(skip_sslcert_validation: bool) -> aiohttp.ClientSession:
    """
    Returns a default aiohttp client session with the default configuration.
    This is used for the API client session when no explicit session is provided.
    """
    ssl: SSLContextType = True
    if skip_sslcert_validation:
        ssl = False
    connector = aiohttp.TCPConnector(ssl=ssl)
    return aiohttp.ClientSession(connector=connector)


class AsyncSession(BaseSession):
    """
    A context manager for API client sessions that makes API requests asynchronously.
    You may call all APIs as coroutines.
    WebSocket-based APIs and SSE-based APIs returns special response types.
    """

    def __init__(
        self,
        *,
        config: Optional[APIConfig] = None,
        proxy_mode: bool = False,
        aiohttp_session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        super().__init__(config=config, proxy_mode=proxy_mode)
        if aiohttp_session is not None:
            self.aiohttp_session = aiohttp_session
            self._owns_session = False
        else:
            self.aiohttp_session = _default_http_client_session(
                self._config.skip_sslcert_validation
            )
            self._owns_session = True

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
        if self._owns_session:
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


# TODO: Remove this after refactoring session management with contextvars
@actxmgr
async def set_api_context(session):
    token = api_session.set(session)
    try:
        yield
    finally:
        api_session.reset(token)
