from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.dependencies.stacks.builder import DependencyBuilderStack
from ai.backend.manager.dependencies.system.background_task_manager import (
    BackgroundTaskManagerDependency,
)
from ai.backend.manager.dependencies.system.composer import (
    SystemComposer,
    SystemInput,
    SystemResources,
)
from ai.backend.manager.dependencies.system.cors_options import CORSOptionsDependency
from ai.backend.manager.dependencies.system.gql_adapter import GQLAdapterDependency
from ai.backend.manager.dependencies.system.health_probe import HealthProbeDependency
from ai.backend.manager.dependencies.system.jwt_validator import JWTValidatorDependency
from ai.backend.manager.dependencies.system.metrics import MetricsDependency
from ai.backend.manager.dependencies.system.prometheus_client import PrometheusClientDependency
from ai.backend.manager.dependencies.system.service_discovery import ServiceDiscoveryDependency


class TestProviderStageNames:
    """Verify stage_name for all providers and the composer."""

    def test_cors_options_stage_name(self) -> None:
        assert CORSOptionsDependency().stage_name == "cors-options"

    def test_metrics_stage_name(self) -> None:
        assert MetricsDependency().stage_name == "metrics"

    def test_gql_adapter_stage_name(self) -> None:
        assert GQLAdapterDependency().stage_name == "gql-adapter"

    def test_jwt_validator_stage_name(self) -> None:
        assert JWTValidatorDependency().stage_name == "jwt-validator"

    def test_prometheus_client_stage_name(self) -> None:
        assert PrometheusClientDependency().stage_name == "prometheus-client"

    def test_service_discovery_stage_name(self) -> None:
        assert ServiceDiscoveryDependency().stage_name == "service-discovery"

    def test_background_task_manager_stage_name(self) -> None:
        assert BackgroundTaskManagerDependency().stage_name == "background-task-manager"

    def test_health_probe_stage_name(self) -> None:
        assert HealthProbeDependency().stage_name == "health-probe"

    def test_system_composer_stage_name(self) -> None:
        assert SystemComposer().stage_name == "system"


class TestSystemComposer:
    """Test SystemComposer lifecycle."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.system.service_discovery.ETCDServiceDiscovery",
    )
    @patch(
        "ai.backend.manager.dependencies.system.service_discovery.ServiceDiscoveryLoop",
    )
    @patch(
        "ai.backend.manager.dependencies.system.prometheus_client.ClientPool",
    )
    @patch(
        "ai.backend.manager.dependencies.system.health_probe.HealthProbe",
    )
    @patch(
        "ai.backend.manager.dependencies.system.health_probe.DatabaseHealthChecker",
    )
    @patch(
        "ai.backend.manager.dependencies.system.health_probe.EtcdHealthChecker",
    )
    @patch(
        "ai.backend.manager.dependencies.system.health_probe.ValkeyHealthChecker",
    )
    async def test_compose_lifecycle(
        self,
        mock_valkey_checker_class: MagicMock,
        mock_etcd_checker_class: MagicMock,
        mock_db_checker_class: MagicMock,
        mock_health_probe_class: MagicMock,
        mock_client_pool_class: MagicMock,
        mock_sd_loop_class: MagicMock,
        mock_etcd_sd_class: MagicMock,
    ) -> None:
        """SystemComposer should initialize all system services and clean up properly."""
        # Setup mock config
        mock_config = MagicMock()
        mock_config.jwt.to_jwt_config.return_value = MagicMock()
        mock_config.metric.address.to_legacy.return_value = "localhost:9090"
        mock_config.service_discovery.type = "etcd"
        mock_config.manager.id = "test-manager"
        mock_config.manager.announce_addr.address = "127.0.0.1"
        mock_config.manager.announce_addr.port = 8080
        mock_config.manager.announce_internal_addr.address = "127.0.0.1"

        # Setup mock infrastructure
        mock_etcd = MagicMock()
        mock_valkey = MagicMock()
        mock_valkey.bgtask = MagicMock()
        mock_valkey.artifact = MagicMock()
        mock_valkey.container_log = MagicMock()
        mock_valkey.live = MagicMock()
        mock_valkey.stat = MagicMock()
        mock_valkey.image = MagicMock()
        mock_valkey.stream = MagicMock()
        mock_valkey.schedule = MagicMock()
        mock_db = MagicMock()
        mock_event_producer = MagicMock()
        mock_valkey_profile_target = MagicMock()

        # Setup mock client pool
        mock_client_pool = MagicMock()
        mock_client_pool.close = AsyncMock()
        mock_client_pool_class.return_value = mock_client_pool

        # Setup mock SD
        mock_etcd_sd = MagicMock()
        mock_etcd_sd_class.return_value = mock_etcd_sd
        mock_sd_loop = MagicMock()
        mock_sd_loop.close = MagicMock()
        mock_sd_loop.metadata = MagicMock()
        mock_sd_loop_class.return_value = mock_sd_loop

        # Setup mock health probe
        mock_probe = MagicMock()
        mock_probe.register = AsyncMock()
        mock_probe.start = AsyncMock()
        mock_probe.stop = AsyncMock()
        mock_health_probe_class.return_value = mock_probe

        # Setup mock BackgroundTaskManager
        with patch(
            "ai.backend.manager.dependencies.system.background_task_manager.BackgroundTaskManager"
        ) as mock_bgtask_class:
            mock_bgtask_manager = MagicMock()
            mock_bgtask_manager.shutdown = AsyncMock()
            mock_bgtask_class.return_value = mock_bgtask_manager

            setup_input = SystemInput(
                config=mock_config,
                etcd=mock_etcd,
                valkey=mock_valkey,
                db=mock_db,
                event_producer=mock_event_producer,
                valkey_profile_target=mock_valkey_profile_target,
            )

            composer = SystemComposer()
            stack = DependencyBuilderStack()

            async with stack:
                async with composer.compose(stack, setup_input) as resources:
                    assert isinstance(resources, SystemResources)

                    # Layer 0
                    assert isinstance(resources.cors_options, dict)
                    assert "*" in resources.cors_options
                    assert resources.metrics is not None
                    assert resources.gql_adapter is not None

                    # Layer 1
                    assert resources.jwt_validator is not None
                    assert resources.prometheus_client is not None
                    assert resources.service_discovery is mock_etcd_sd
                    assert resources.sd_loop is mock_sd_loop

                    # Layer 3
                    assert resources.background_task_manager is mock_bgtask_manager

                    # Layer 4
                    assert resources.health_probe is mock_probe

            # Verify cleanup was called
            mock_client_pool.close.assert_awaited_once()
            mock_sd_loop.close.assert_called_once()
            mock_bgtask_manager.shutdown.assert_awaited_once()
            mock_probe.stop.assert_awaited_once()
