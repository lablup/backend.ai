from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    BinarySize,
    DeviceId,
    QuotaScopeID,
    QuotaScopeType,
    RuntimeVariant,
    SessionId,
    SlotName,
    VFolderID,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry

if TYPE_CHECKING:
    from collections.abc import Iterator


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
        scheduling_controller=mock_scheduling_controller,  # type: ignore
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


@pytest.mark.asyncio
async def test_convert_resource_spec_to_resource_slot(
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, ManagerConfigProvider, MagicMock, MagicMock
    ],
) -> None:
    registry, _, _, _, _, _, _ = registry_ctx
    allocations = {
        "cuda": {
            SlotName("cuda.shares"): {
                DeviceId("a0"): "2.5",
                DeviceId("a1"): "2.0",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cuda.shares"] == Decimal("4.5")
    allocations = {
        "cpu": {
            SlotName("cpu"): {
                DeviceId("a0"): "3",
                DeviceId("a1"): "1",
            },
        },
        "ram": {
            SlotName("ram"): {
                DeviceId("b0"): "2.5g",
                DeviceId("b1"): "512m",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cpu"] == Decimal("4")
    assert converted_allocations["ram"] == Decimal(BinarySize.from_str("1g")) * 3


@dataclass
class MockEndpointData:
    """Mock EndpointData for testing."""

    runtime_variant: RuntimeVariant
    model_definition_path: str | None = None


@dataclass
class MockVFolderRow:
    """Mock VFolderRow for testing."""

    host: str
    vfid: VFolderID


@dataclass
class MockDeploymentConfig:
    """Mock deployment config for testing."""

    enable_model_definition_override: bool = False


@dataclass
class MockConfig:
    """Mock config for testing."""

    deployment: MockDeploymentConfig


@dataclass
class MockConfigProvider:
    """Mock config provider for testing."""

    config: MockConfig


@dataclass
class HealthCheckTestCase:
    """Test case for health check configuration."""

    input: dict[str, float | int | str]
    expected_path: str
    expected_interval: float = 10.0
    expected_max_retries: int = 10
    expected_max_wait_time: float = 15.0
    expected_status_code: int = 200
    expected_initial_delay: float = 60.0


class TestGetHealthCheckInfo:
    """Tests for get_health_check_info method."""

    @pytest.fixture
    def mock_storage_manager(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_config_provider(self) -> MockConfigProvider:
        return MockConfigProvider(
            config=MockConfig(
                deployment=MockDeploymentConfig(enable_model_definition_override=False)
            )
        )

    @pytest.fixture
    def mock_endpoint_custom(self) -> MockEndpointData:
        return MockEndpointData(
            runtime_variant=RuntimeVariant.CUSTOM,
            model_definition_path="model-definition.yaml",
        )

    @pytest.fixture
    def mock_vfolder(self) -> MockVFolderRow:
        quota_scope_id = QuotaScopeID(QuotaScopeType.PROJECT, uuid.uuid4())
        return MockVFolderRow(
            host="local",
            vfid=VFolderID(quota_scope_id=quota_scope_id, folder_id=uuid.uuid4()),
        )

    @pytest.fixture
    def patch_model_service_helper(self) -> Iterator[AsyncMock]:
        """Patch ModelServiceHelper methods for testing."""
        with (
            patch(
                "ai.backend.manager.registry.ModelServiceHelper.validate_model_definition_file_exists",
                new_callable=AsyncMock,
                return_value="model-definition.yaml",
            ),
            patch(
                "ai.backend.manager.registry.ModelServiceHelper.validate_model_definition",
                new_callable=AsyncMock,
            ) as mock_validate_definition,
        ):
            yield mock_validate_definition

    @pytest.fixture
    def mock_registry(
        self,
        mock_storage_manager: AsyncMock,
        mock_config_provider: MockConfigProvider,
    ) -> MagicMock:
        """Create a mock AgentRegistry with required dependencies."""
        registry = MagicMock(spec=AgentRegistry)
        registry.storage_manager = mock_storage_manager
        registry.config_provider = mock_config_provider
        return registry

    @pytest.mark.parametrize(
        "test_case",
        [
            HealthCheckTestCase(
                input={
                    "path": "/custom-health",
                    "interval": 5.0,
                    "max_retries": 3,
                    "max_wait_time": 30.0,
                    "expected_status_code": 201,
                    "initial_delay": 120.0,
                },
                expected_path="/custom-health",
                expected_interval=5.0,
                expected_max_retries=3,
                expected_max_wait_time=30.0,
                expected_status_code=201,
                expected_initial_delay=120.0,
            ),
            HealthCheckTestCase(
                input={
                    "path": "/health",
                    "interval": 10.0,
                    "max_retries": 5,
                    "max_wait_time": 20.0,
                    "expected_status_code": 200,
                    # initial_delay omitted - should use Pydantic default (60.0)
                },
                expected_path="/health",
                expected_interval=10.0,
                expected_max_retries=5,
                expected_max_wait_time=20.0,
                expected_status_code=200,
                expected_initial_delay=60.0,
            ),
            HealthCheckTestCase(
                input={"path": "/health"},
                # All optional fields use Pydantic defaults
                expected_path="/health",
                expected_interval=10.0,
                expected_max_retries=10,
                expected_max_wait_time=15.0,
                expected_status_code=200,
                expected_initial_delay=60.0,
            ),
        ],
    )
    async def test_custom_variant_health_check_config(
        self,
        mock_registry: MagicMock,
        mock_endpoint_custom: MockEndpointData,
        mock_vfolder: MockVFolderRow,
        patch_model_service_helper: AsyncMock,
        test_case: HealthCheckTestCase,
    ) -> None:
        """Test CUSTOM variant with various health check configurations."""
        mock_validate_definition = patch_model_service_helper
        mock_validate_definition.return_value = {
            "models": [{"service": {"health_check": test_case.input}}]
        }

        result = await AgentRegistry.get_health_check_info(
            mock_registry,
            mock_endpoint_custom,  # type: ignore[arg-type]
            mock_vfolder,  # type: ignore[arg-type]
        )

        assert result is not None
        assert result.path == test_case.expected_path
        assert result.interval == test_case.expected_interval
        assert result.max_retries == test_case.expected_max_retries
        assert result.max_wait_time == test_case.expected_max_wait_time
        assert result.expected_status_code == test_case.expected_status_code
        assert result.initial_delay == test_case.expected_initial_delay

    async def test_custom_variant_without_health_check_returns_none(
        self,
        mock_registry: MagicMock,
        mock_endpoint_custom: MockEndpointData,
        mock_vfolder: MockVFolderRow,
        patch_model_service_helper: AsyncMock,
    ) -> None:
        """Test CUSTOM variant without health_check in model definition returns None."""
        mock_validate_definition = patch_model_service_helper
        mock_validate_definition.return_value = {
            "models": [{"service": {}}]  # No health_check defined
        }

        result = await AgentRegistry.get_health_check_info(
            mock_registry,
            mock_endpoint_custom,  # type: ignore[arg-type]
            mock_vfolder,  # type: ignore[arg-type]
        )

        assert result is None

    async def test_vllm_variant_returns_default_health_check(
        self,
        mock_registry: MagicMock,
        mock_vfolder: MockVFolderRow,
    ) -> None:
        """Test VLLM variant returns default health check endpoint from profile."""
        endpoint = MockEndpointData(
            runtime_variant=RuntimeVariant.VLLM,
            model_definition_path=None,
        )

        result = await AgentRegistry.get_health_check_info(
            mock_registry,
            endpoint,  # type: ignore[arg-type]
            mock_vfolder,  # type: ignore[arg-type]
        )

        assert result is not None
        expected_path = MODEL_SERVICE_RUNTIME_PROFILES[RuntimeVariant.VLLM].health_check_endpoint
        assert result.path == expected_path
