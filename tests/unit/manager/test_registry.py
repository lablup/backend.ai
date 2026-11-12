from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dateutil.tz import tzutc

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.config import (
    ModelConfig,
    ModelDefinition,
    ModelHealthCheck,
    ModelServiceConfig,
)
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.defs.session import JOB_PRIORITY_DEFAULT, SESSION_PRIORITY_DEFAULT
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.types import AbstractEvent
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.options import SessionStoredOptions
from ai.backend.manager.data.session.types import SessionEntityData, SessionStatus
from ai.backend.manager.errors.kernel import (
    MainKernelNotFound,
    SessionAlreadyExists,
    SessionNotFound,
    TooManyKernelsFound,
)
from ai.backend.manager.models.session.searchers import LiveSessionsNamedSearcher
from ai.backend.manager.models.specs.searcher import SearcherResult
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.types import UserScope


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}

    async def get(self, key: str) -> Any:
        return None


@pytest.fixture
async def registry_ctx() -> AsyncGenerator[
    tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, ManagerConfigProvider, MagicMock, MagicMock
    ],
    None,
]:
    mocked_etcd = DummyEtcd()
    mock_etcd_config_loader = MagicMock()
    mock_etcd_config_loader.update_resource_slots = AsyncMock()
    mock_etcd_config_loader._etcd = mocked_etcd

    mock_loader = MagicMock()
    mock_loader.load = AsyncMock(
        return_value={
            "db": {"name": "test_db", "user": "postgres", "password": "develove"},
            "etcd": {"user": "test", "password": "test"},
            "logging": {},
        }
    )
    mock_config_provider = await ManagerConfigProvider.create(
        loader=mock_loader,
        etcd_watcher=MagicMock(),
        legacy_etcd_config_loader=mock_etcd_config_loader,
    )
    mock_db = MagicMock()
    mock_dbconn = MagicMock()
    mock_dbsess = MagicMock()
    mock_dbconn_ctx = MagicMock()
    mock_dbsess_ctx = MagicMock()
    mock_dbresult = MagicMock()
    mock_dbresult.rowcount = 1
    mock_agent_cache = MagicMock()
    mock_db.connect = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin_session = MagicMock(return_value=mock_dbsess_ctx)
    mock_dbconn_ctx.__aenter__ = AsyncMock(return_value=mock_dbconn)
    mock_dbconn_ctx.__aexit__ = AsyncMock()
    mock_dbsess_ctx.__aenter__ = AsyncMock(return_value=mock_dbsess)
    mock_dbsess_ctx.__aexit__ = AsyncMock()
    mock_dbconn.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbconn.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_dbsess.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbsess.begin_session = AsyncMock(return_value=mock_dbsess_ctx)
    mock_valkey_stat_client = MagicMock()
    mock_redis_live = MagicMock()
    mock_redis_live.hset = AsyncMock()
    mock_redis_image = AsyncMock()
    mock_redis_image.close = AsyncMock()
    mock_redis_image.get_all_agents_images = AsyncMock(return_value=[])
    mock_redis_image.get_agent_images = AsyncMock(return_value=[])
    mock_redis_image.add_agent_image = AsyncMock()
    mock_redis_image.remove_agent_image = AsyncMock()
    mock_redis_image.remove_agent = AsyncMock()
    mock_redis_image.clear_all_images = AsyncMock()
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()
    mock_event_producer.anycast_event = AsyncMock()
    mock_event_producer.broadcast_event = AsyncMock()
    mock_event_producer.anycast_and_broadcast_event = AsyncMock()

    mock_event_hub = MagicMock()
    mock_event_hub.publish = AsyncMock()
    mock_event_hub.subscribe = AsyncMock()
    mock_event_hub.unsubscribe = AsyncMock()

    hook_plugin_ctx = HookPluginContext(mocked_etcd, {})  # type: ignore
    network_plugin_ctx = NetworkPluginContext(mocked_etcd, {})  # type: ignore

    mock_scheduling_controller = AsyncMock()
    mock_scheduling_controller.enqueue_session = AsyncMock(return_value=SessionId(uuid.uuid4()))
    mock_scheduling_controller.dispatch_session_events = AsyncMock()

    mock_agent_client_pool = MagicMock()

    registry = AgentRegistry(
        config_provider=mock_config_provider,
        db=mock_db,
        agent_cache=mock_agent_cache,
        agent_client_pool=mock_agent_client_pool,
        valkey_stat=mock_valkey_stat_client,
        valkey_live=mock_redis_live,
        valkey_image=mock_redis_image,
        event_producer=mock_event_producer,
        event_hub=mock_event_hub,
        storage_manager=None,  # type: ignore
        hook_plugin_ctx=hook_plugin_ctx,
        network_plugin_ctx=network_plugin_ctx,
        scheduling_controller=mock_scheduling_controller,
        scheduler_repository=MagicMock(),
        ops_provider=MagicMock(),
        manager_public_key=PublicKey(b"GqK]ZYY#h*9jAQbGxSwkeZX3Y*%b+DiY$7ju6sh{"),
        manager_secret_key=SecretKey(b"37KX6]ac^&hcnSaVo=-%eVO9M]ENe8v=BOWF(Sw$"),
    )
    await registry.init()
    try:
        yield (
            registry,
            mock_dbconn,
            mock_dbsess,
            mock_dbresult,
            mock_config_provider,
            mock_event_dispatcher,
            mock_event_producer,
        )
    finally:
        await registry.shutdown()


@dataclass
class MockEndpointData:
    """Minimal stand-in for ``EndpointData`` exposing only ``model_definition``.

    The runtime health-check path reads exactly that field — the persisted
    merged result from the revision — and nothing else.
    """

    model_definition: ModelDefinition | None


class TestResolveHealthCheck:
    """Tests for ``AgentRegistry._resolve_health_check``."""

    def test_returns_stored_health_check(self) -> None:
        endpoint = MockEndpointData(
            model_definition=ModelDefinition(
                models=[
                    ModelConfig(
                        name="m",
                        model_path="/models/m",
                        service=ModelServiceConfig(
                            start_command="run",
                            port=8000,
                            health_check=ModelHealthCheck(
                                enable=True,
                                path="/custom",
                                interval=5.0,
                                max_retries=3,
                                max_wait_time=30.0,
                                expected_status_code=201,
                                initial_delay=120.0,
                            ),
                        ),
                    )
                ]
            )
        )
        result = AgentRegistry._resolve_health_check(endpoint)  # type: ignore[arg-type]
        assert result is not None
        assert result.path == "/custom"
        assert result.interval == 5.0
        assert result.max_retries == 3
        assert result.max_wait_time == 30.0
        assert result.expected_status_code == 201
        assert result.initial_delay == 120.0

    def test_returns_none_when_no_model_definition(self) -> None:
        endpoint = MockEndpointData(model_definition=None)
        assert AgentRegistry._resolve_health_check(endpoint) is None  # type: ignore[arg-type]

    def test_returns_none_when_no_health_check_in_definition(self) -> None:
        endpoint = MockEndpointData(
            model_definition=ModelDefinition(
                models=[
                    ModelConfig(
                        name="m",
                        model_path="/models/m",
                        service=ModelServiceConfig(start_command="run", port=8000),
                    )
                ]
            )
        )
        assert AgentRegistry._resolve_health_check(endpoint) is None  # type: ignore[arg-type]


def _make_scheduling_event(
    session_id: SessionId,
    status: str,
) -> SchedulingBroadcastEvent:
    return SchedulingBroadcastEvent(
        session_id=session_id,
        creation_id="test-creation",
        status_transition=status,
        reason="test",
    )


class TestResourceEntriesFromLegacyDict:
    """Tests for ``AgentRegistry._resource_entries_from_legacy_dict``."""

    def test_drops_zero_quantity_slots(self) -> None:
        entries = AgentRegistry._resource_entries_from_legacy_dict({
            "cpu": 1,
            "mem": "1140850688",
            "cuda.device": 0,
            "cuda.shares": "0",
        })
        assert {str(e.resource_type): e.quantity for e in entries} == {
            "cpu": "1",
            "mem": "1140850688",
        }

    def test_normalizes_binary_size_shortcuts(self) -> None:
        entries = AgentRegistry._resource_entries_from_legacy_dict({
            "mem": "1g",
            "cuda.shares": "0.5",
        })
        assert {str(e.resource_type): e.quantity for e in entries} == {
            "mem": str(1024**3),
            "cuda.shares": "0.5",
        }


class TestWaitForSessionRunning:
    """Tests for _wait_for_session_running() timeout behavior."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid.uuid4())

    @pytest.fixture
    def mock_propagator(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_registry_obj(self) -> MagicMock:
        """Create a minimal mock with db for the registry instance."""
        registry = MagicMock(spec=AgentRegistry)
        registry._wait_for_session_running = AgentRegistry._wait_for_session_running.__get__(
            registry, AgentRegistry
        )
        return registry

    async def test_max_wait_positive_times_out_after_specified_seconds(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """max_wait=2 should raise TimeoutError after ~2 seconds, not 60."""

        async def _hang_forever(cache_id: str) -> AsyncIterator[AbstractEvent]:
            await asyncio.Event().wait()  # blocks until cancelled by timeout
            yield  # type: ignore[misc]  # make it an async generator

        mock_propagator.receive = _hang_forever

        start = time.monotonic()
        with pytest.raises(TimeoutError):
            await mock_registry_obj._wait_for_session_running(
                session_id, mock_propagator, max_wait=2
            )
        elapsed = time.monotonic() - start
        assert elapsed < 5, f"Timed out in {elapsed}s, expected ~2s"
        assert elapsed >= 1.5, f"Timed out too fast in {elapsed}s, expected ~2s"

    async def test_max_wait_zero_uses_default_timeout_and_retries(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """max_wait=0 should NOT raise TimeoutError; it retries after timeout and checks DB."""
        call_count = 0

        async def _hang_then_stop(cache_id: str) -> AsyncIterator[AbstractEvent]:
            nonlocal call_count
            call_count += 1
            await asyncio.Event().wait()
            yield  # type: ignore[misc]

        mock_propagator.receive = _hang_then_stop

        # Mock DB to return RUNNING status on the fallback check
        mock_db_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.status = SessionStatus.RUNNING
        mock_result.first.return_value = mock_row
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        mock_db_ctx = MagicMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_registry_obj.db = MagicMock()
        mock_registry_obj.db.begin_readonly_session = MagicMock(return_value=mock_db_ctx)

        # With max_wait=0, the method should catch TimeoutError, check DB, and return
        # We use a short timeout by patching DEFAULT_WAIT_TIMEOUT_SECONDS
        with patch("ai.backend.manager.registry.DEFAULT_WAIT_TIMEOUT_SECONDS", 1):
            await mock_registry_obj._wait_for_session_running(
                session_id, mock_propagator, max_wait=0
            )

        assert call_count >= 1

    async def test_running_event_returns_immediately(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """Session becoming RUNNING should cause immediate return."""

        async def _yield_running(cache_id: str) -> AsyncIterator[AbstractEvent]:
            yield _make_scheduling_event(session_id, str(SessionStatus.RUNNING))

        mock_propagator.receive = _yield_running

        start = time.monotonic()
        await mock_registry_obj._wait_for_session_running(session_id, mock_propagator, max_wait=15)
        elapsed = time.monotonic() - start
        assert elapsed < 1, f"Should return immediately, took {elapsed}s"

    async def test_max_wait_zero_db_not_found_raises_session_not_found(
        self,
        session_id: SessionId,
        mock_propagator: MagicMock,
        mock_registry_obj: MagicMock,
    ) -> None:
        """max_wait=0 timeout + session not found in DB should raise SessionNotFound."""

        async def _hang(cache_id: str) -> AsyncIterator[AbstractEvent]:
            await asyncio.Event().wait()
            yield  # type: ignore[misc]

        mock_propagator.receive = _hang

        mock_db_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None  # session not found in DB
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        mock_db_ctx = MagicMock()
        mock_db_ctx.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_registry_obj.db = MagicMock()
        mock_registry_obj.db.begin_readonly_session = MagicMock(return_value=mock_db_ctx)

        with patch("ai.backend.manager.registry.DEFAULT_WAIT_TIMEOUT_SECONDS", 1):
            with pytest.raises(SessionNotFound):
                await mock_registry_obj._wait_for_session_running(
                    session_id, mock_propagator, max_wait=0
                )


def _session_entity_data(name: str, access_key: AccessKey) -> SessionEntityData:
    """A running session of ``access_key`` named ``name``."""
    return SessionEntityData(
        id=SessionID(uuid.uuid4()),
        creation_id=None,
        name=name,
        session_type=SessionTypes.INTERACTIVE,
        priority=SESSION_PRIORITY_DEFAULT,
        is_preemptible=True,
        job_priority=JOB_PRIORITY_DEFAULT,
        cluster_mode=ClusterMode.SINGLE_NODE.value,
        cluster_size=1,
        options=SessionStoredOptions(),
        agent_ids=None,
        session_group_id=None,
        resource_group_id=ResourceGroupID(uuid.uuid4()),
        resource_group_name="default",
        target_sgroup_names=None,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
        group_id=ProjectID(uuid.uuid4()),
        user_uuid=UserID(uuid.uuid4()),
        access_key=access_key,
        images=None,
        image_ids=None,
        tag=None,
        vfolder_mounts=None,
        environ=None,
        bootstrap_script=None,
        use_host_network=False,
        timeout=None,
        batch_timeout=None,
        terminated_at=None,
        starts_at=None,
        requested_starts_at=None,
        status=SessionStatus.RUNNING,
        status_info=None,
        status_data=None,
        status_history=None,
        callback_url=None,
        startup_command=None,
        result=SessionResult.UNDEFINED,
        num_queries=None,
        last_stat=None,
        network_type=None,
        network_id=None,
        replica_id=None,
        created_at=datetime.now(tzutc()),
    )


def _read_ops_answering(items: list[SessionEntityData]) -> MagicMock:
    """Read ops that answer every global search with ``items``."""
    read_ops = MagicMock()
    read_ops.search_in_global = AsyncMock(
        return_value=SearcherResult(
            items=items, total_count=len(items), has_next_page=False, has_previous_page=False
        )
    )
    return read_ops


class TestLiveSessionNamed:
    @pytest.fixture
    def access_key(self) -> AccessKey:
        return AccessKey("AKIATEST")

    @pytest.fixture
    def registry(
        self,
        registry_ctx: tuple[
            AgentRegistry,
            MagicMock,
            MagicMock,
            MagicMock,
            ManagerConfigProvider,
            MagicMock,
            MagicMock,
        ],
    ) -> AgentRegistry:
        return registry_ctx[0]

    async def test_none_when_no_live_session_carries_the_name(
        self, registry: AgentRegistry, access_key: AccessKey
    ) -> None:
        read_ops = _read_ops_answering([])

        assert await registry._live_session_named(read_ops, "fresh", access_key) is None

    async def test_returns_the_one_session_carrying_the_name(
        self, registry: AgentRegistry, access_key: AccessKey
    ) -> None:
        session = _session_entity_data("taken", access_key)
        read_ops = _read_ops_answering([session])

        assert await registry._live_session_named(read_ops, "taken", access_key) is session


class TestCreateSessionWithLiveNamesake:
    """`create_session` when a live session already carries the requested name."""

    @pytest.fixture
    def access_key(self) -> AccessKey:
        return AccessKey("AKIATEST")

    @pytest.fixture
    def existing(self, access_key: AccessKey) -> SessionEntityData:
        return _session_entity_data("taken", access_key)

    @pytest.fixture
    def image_ref(self) -> MagicMock:
        image_ref = MagicMock()
        image_ref.is_local = True
        return image_ref

    @pytest.fixture
    def main_kernel(self) -> MagicMock:
        main_kernel = MagicMock()
        main_kernel.network.service_ports = [{"name": "jupyter"}]
        return main_kernel

    @pytest.fixture
    def registry(
        self,
        registry_ctx: tuple[
            AgentRegistry,
            MagicMock,
            MagicMock,
            MagicMock,
            ManagerConfigProvider,
            MagicMock,
            MagicMock,
        ],
    ) -> AgentRegistry:
        return registry_ctx[0]

    def _answer_reads(
        self,
        registry: AgentRegistry,
        existing: SessionEntityData,
        main_kernels: list[MagicMock],
        running_image_ref: MagicMock,
    ) -> None:
        """Answer the session, main kernel and image reads of `create_session`."""
        image = MagicMock()
        image.customized = False
        image.image_ref = running_image_ref

        async def search_in_global(searcher: Any) -> SearcherResult[Any]:
            items: list[Any]
            match searcher:
                case LiveSessionsNamedSearcher():
                    items = [existing]
                case _:
                    items = [image]
            return SearcherResult(
                items=items, total_count=len(items), has_next_page=False, has_previous_page=False
            )

        async def search_with_scopes(scopes: Any, searcher: Any) -> SearcherResult[Any]:
            items = list(main_kernels)
            return SearcherResult(
                items=items, total_count=len(items), has_next_page=False, has_previous_page=False
            )

        read_ops = MagicMock()
        read_ops.search_in_global = search_in_global
        read_ops.search_with_scopes = search_with_scopes

        @asynccontextmanager
        async def open_read_ops() -> AsyncIterator[MagicMock]:
            yield read_ops

        ops_provider = MagicMock()
        ops_provider.read_ops = open_read_ops
        registry._ops_provider = ops_provider

    async def _create_session(
        self, registry: AgentRegistry, access_key: AccessKey, image_ref: MagicMock, *, reuse: bool
    ) -> Mapping[str, Any]:
        return await registry.create_session(
            "taken",
            image_ref,
            UserScope(
                domain_name="default",
                group_id=uuid.uuid4(),
                user_uuid=uuid.uuid4(),
                user_role="user",
            ),
            access_key,
            {},
            SessionTypes.INTERACTIVE,
            {"resources": None},
            ClusterMode.SINGLE_NODE,
            1,
            reuse=reuse,
        )

    async def test_reuse_returns_the_live_session(
        self,
        registry: AgentRegistry,
        access_key: AccessKey,
        existing: SessionEntityData,
        image_ref: MagicMock,
        main_kernel: MagicMock,
    ) -> None:
        self._answer_reads(registry, existing, [main_kernel], image_ref)

        resp = await self._create_session(registry, access_key, image_ref, reuse=True)

        assert resp == {
            "sessionId": str(existing.id),
            "sessionName": "taken",
            "status": existing.status.name,
            "service_ports": [{"name": "jupyter"}],
            "servicePorts": [{"name": "jupyter"}],
            "created": False,
        }

    async def test_without_reuse_raises_already_exists(
        self,
        registry: AgentRegistry,
        access_key: AccessKey,
        existing: SessionEntityData,
        image_ref: MagicMock,
        main_kernel: MagicMock,
    ) -> None:
        self._answer_reads(registry, existing, [main_kernel], image_ref)

        with pytest.raises(SessionAlreadyExists) as exc_info:
            await self._create_session(registry, access_key, image_ref, reuse=False)

        assert exc_info.value.extra_data == {"existingSessionId": str(existing.id)}

    async def test_reuse_with_another_image_raises_already_exists(
        self,
        registry: AgentRegistry,
        access_key: AccessKey,
        existing: SessionEntityData,
        image_ref: MagicMock,
        main_kernel: MagicMock,
    ) -> None:
        self._answer_reads(registry, existing, [main_kernel], MagicMock())

        with pytest.raises(SessionAlreadyExists) as exc_info:
            await self._create_session(registry, access_key, image_ref, reuse=True)

        assert exc_info.value.extra_data == {"existingSessionId": str(existing.id)}

    async def test_no_main_kernel_raises_main_kernel_not_found(
        self,
        registry: AgentRegistry,
        access_key: AccessKey,
        existing: SessionEntityData,
        image_ref: MagicMock,
    ) -> None:
        self._answer_reads(registry, existing, [], image_ref)

        with pytest.raises(MainKernelNotFound):
            await self._create_session(registry, access_key, image_ref, reuse=True)

    async def test_several_main_kernels_raise_too_many_kernels_found(
        self,
        registry: AgentRegistry,
        access_key: AccessKey,
        existing: SessionEntityData,
        image_ref: MagicMock,
        main_kernel: MagicMock,
    ) -> None:
        self._answer_reads(registry, existing, [main_kernel, MagicMock()], image_ref)

        with pytest.raises(TooManyKernelsFound):
            await self._create_session(registry, access_key, image_ref, reuse=True)
