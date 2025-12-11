import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.route.coordinator import (
    RouteCoordinator,
    RouteLifecycleType,
)
from ai.backend.manager.sokovan.deployment.route.handlers.provisioning import (
    ProvisioningRouteHandler,
)


class TestHandlerLockConcurrency:
    """Test cases for handler lock ID concurrency control"""

    @pytest.fixture
    def execution_log(self) -> list[tuple[str, float, int]]:
        """Shared execution log for tracking concurrent executions (event, time, call_id)"""
        return []

    @pytest.fixture
    def concurrent_execution_flag(self) -> dict[str, bool]:
        """Flag to detect concurrent execution"""
        return {"is_executing": False}

    @pytest.fixture
    def lock_acquired_count(self) -> dict[str, int]:
        """Counter for lock acquisitions (using dict for mutability in closures)"""
        return {"count": 0}

    @pytest.fixture
    def mock_lock_context(self, lock_acquired_count: dict[str, int]) -> Any:
        """Mock lock context manager that actually enforces mutual exclusion"""
        # Use a real asyncio.Lock to enforce mutual exclusion in tests
        real_lock = asyncio.Lock()

        @asynccontextmanager
        async def _mock_lock_context(lock_id: LockID, lifetime: float):
            lock_acquired_count["count"] += 1
            async with real_lock:
                yield None

        return _mock_lock_context

    @pytest.fixture
    def mock_route_executor(
        self,
        execution_log: list[tuple[str, float, int]],
        concurrent_execution_flag: dict[str, bool],
    ) -> MagicMock:
        """Mock RouteExecutor with provision_routes that simulates work"""
        call_counter = {"count": 0}

        async def mock_provision_routes(routes):
            """Simulate work that takes time and detect concurrent execution"""
            call_id = call_counter["count"]
            call_counter["count"] += 1

            # Check if another execution is in progress (should not happen with lock)
            if concurrent_execution_flag["is_executing"]:
                execution_log.append(("concurrent_detected", time.time(), call_id))

            concurrent_execution_flag["is_executing"] = True
            await asyncio.sleep(0.1)  # Simulate work
            concurrent_execution_flag["is_executing"] = False

            return MagicMock(successes=[], errors=[])

        mock_executor = MagicMock()
        mock_executor.provision_routes = AsyncMock(side_effect=mock_provision_routes)
        return mock_executor

    @pytest.fixture
    def provisioning_handler(self, mock_route_executor: MagicMock) -> ProvisioningRouteHandler:
        """Real ProvisioningRouteHandler instance with mocked executor"""
        mock_event_producer = MagicMock()
        return ProvisioningRouteHandler(mock_route_executor, mock_event_producer)

    @pytest.fixture
    async def route_coordinator(
        self, mock_lock_context: Any, provisioning_handler: ProvisioningRouteHandler
    ) -> AsyncGenerator[RouteCoordinator, None]:
        """Create RouteCoordinator with real ProvisioningRouteHandler"""
        mock_lock_factory = MagicMock(side_effect=mock_lock_context)
        mock_valkey = AsyncMock()
        mock_deployment_repo = AsyncMock()
        mock_deployment_repo.get_routes_by_statuses = AsyncMock(return_value=[])
        mock_event_producer = MagicMock()
        mock_config_provider = MagicMock()
        mock_config_provider.config.manager.session_schedule_lock_lifetime = 1.0

        coordinator = RouteCoordinator(
            valkey_schedule=mock_valkey,
            deployment_repository=mock_deployment_repo,
            event_producer=mock_event_producer,
            lock_factory=mock_lock_factory,
            config_provider=mock_config_provider,
            scheduling_controller=MagicMock(),
            client_pool=MagicMock(),
            service_discovery=MagicMock(),
        )
        coordinator._route_handlers = {RouteLifecycleType.PROVISIONING: provisioning_handler}

        yield coordinator

    @pytest.mark.asyncio
    async def test_concurrent_execution_prevented_by_lock(
        self,
        route_coordinator: RouteCoordinator,
        execution_log: list[tuple[str, float, int]],
        lock_acquired_count: dict[str, int],
    ) -> None:
        """
        Integration test: Verify that lock prevents concurrent execution.

        This test simulates the scenario where short cycle and long cycle
        try to execute the same handler concurrently. With lock_id, the second
        execution should wait for the first one to complete.
        """
        # Execute two concurrent calls (simulating short cycle + long cycle)
        await asyncio.gather(
            route_coordinator.process_route_lifecycle(RouteLifecycleType.PROVISIONING),
            route_coordinator.process_route_lifecycle(RouteLifecycleType.PROVISIONING),
        )

        # Verify both executions happened
        assert lock_acquired_count["count"] == 2  # Lock acquired twice

        # Verify NO concurrent execution was detected
        concurrent_detected = [log for log in execution_log if log[0] == "concurrent_detected"]
        assert len(concurrent_detected) == 0, (
            "Concurrent execution detected! Lock did not prevent simultaneous execution. "
            f"Execution log: {execution_log}"
        )
