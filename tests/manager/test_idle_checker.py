from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Mapping, Optional, Type, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.backend.common import msgpack
from ai.backend.common.types import KernelId, SessionId, SessionTypes
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.idle import (
    BaseIdleChecker,
    IdleCheckerArgs,
    IdleCheckerHost,
    NetworkTimeoutIdleChecker,
    NewUserGracePeriodChecker,
    SessionLifetimeChecker,
    UtilizationIdleChecker,
    calculate_remaining_time,
    init_idle_checkers,
)
from ai.backend.manager.server import (
    background_task_ctx,
    config_provider_ctx,
    database_ctx,
    distributed_lock_ctx,
    event_dispatcher_ctx,
    redis_ctx,
)


def get_checker_from_host(
    checker_host: IdleCheckerHost, checker_type: Type[BaseIdleChecker]
) -> BaseIdleChecker:
    for checker in checker_host._checkers:
        if isinstance(checker, checker_type):
            return checker
    else:
        raise ValueError(
            f"{checker_type} not found in the checker_host. {checker_host._checkers = }"
        )


@dataclass
class _RemainingTimeCalculationTestConfig:
    now: datetime
    idle_baseline: datetime
    timeout_period: timedelta
    grace_period_end: Optional[datetime]
    expected_remaining: float


@pytest.mark.parametrize(
    "remaining_time_config",
    [
        # test 1
        # now + 10.0 == idle_baseline + timeout_period
        _RemainingTimeCalculationTestConfig(
            now=datetime(2020, 3, 1, 12, 30, second=20),
            idle_baseline=datetime(2020, 3, 1, 12, 30, second=0),
            timeout_period=timedelta(seconds=30),
            grace_period_end=None,
            expected_remaining=10.0,
        ),
        # test 2
        # now + 40.0 == max(grace_period_end, idle_baseline) + timeout_period
        _RemainingTimeCalculationTestConfig(
            now=datetime(2020, 3, 1, 12, 30, second=20),
            idle_baseline=datetime(2020, 3, 1, 12, 30, second=0),
            timeout_period=timedelta(seconds=30),
            grace_period_end=datetime(2020, 3, 1, 12, 30, second=30),
            expected_remaining=40.0,
        ),
        # test 3
        _RemainingTimeCalculationTestConfig(
            now=datetime(2020, 3, 1, 12, 30, second=20),
            idle_baseline=datetime(2020, 3, 1, 12, 30, second=30),
            timeout_period=timedelta(seconds=30),
            grace_period_end=datetime(2020, 3, 1, 12, 30, second=20),
            expected_remaining=40.0,
        ),
        # test 4
        # now - 30.0 == max(grace_period_end, idle_baseline) + timeout_period
        _RemainingTimeCalculationTestConfig(
            now=datetime(2020, 3, 1, 12, 30, second=50),
            idle_baseline=datetime(2020, 3, 1, 12, 30, second=0),
            timeout_period=timedelta(seconds=10),
            grace_period_end=datetime(2020, 3, 1, 12, 30, second=10),
            expected_remaining=-30.0,
        ),
    ],
)
@pytest.mark.asyncio
async def remaining_time_calculation(
    remaining_time_config: _RemainingTimeCalculationTestConfig,
) -> None:
    remaining = calculate_remaining_time(
        remaining_time_config.now,
        remaining_time_config.idle_baseline,
        remaining_time_config.timeout_period,
        remaining_time_config.grace_period_end,
    )

    assert remaining == remaining_time_config.expected_remaining


class TestNewUserGracePeriodChecker:
    @pytest.fixture
    def base_time(self) -> datetime:
        """Reference time for all tests. All other times are calculated as offsets from this."""
        return datetime.now(timezone.utc).replace(microsecond=0)

    @pytest.fixture
    async def test_valkey_live(self) -> AsyncMock:
        """Mock ValkeyLiveClient - configure return values in scenario fixtures"""
        mock_client = AsyncMock()
        # Configure default return values
        mock_client.count_active_connections.return_value = 0
        mock_client.get_live_data.return_value = None
        mock_client.get_server_time.return_value = 0.0
        # store_live_data should not raise errors
        mock_client.store_live_data.return_value = None
        return mock_client

    @pytest.fixture
    async def test_valkey_stat(self) -> AsyncMock:
        """Mock ValkeyStatClient - configure return values in scenario fixtures"""
        return AsyncMock()

    @pytest.fixture
    async def mock_event_producer(self) -> AsyncMock:
        """Mock EventProducer"""
        return AsyncMock()

    @pytest.fixture
    async def mock_db_connection(self) -> AsyncMock:
        """Mock database connection"""
        return AsyncMock()

    @pytest.fixture
    def session_id(self) -> SessionId:
        """Session ID for session lifetime tests"""
        return SessionId(uuid4())

    @pytest.fixture
    def kernel_row(self, session_id: SessionId) -> dict[str, Any]:
        """Kernel row for network timeout positive test"""
        return {
            "session_id": session_id,
            "session_type": SessionTypes.INTERACTIVE,
        }

    @pytest.fixture
    def _create_idle_checker_args(
        self,
        mock_event_producer: AsyncMock,
        test_valkey_live: AsyncMock,
        test_valkey_stat: AsyncMock,
    ) -> Callable[[], IdleCheckerArgs]:
        """Internal helper: Create IdleCheckerArgs with standard dependencies"""

        def _create() -> IdleCheckerArgs:
            return IdleCheckerArgs(
                event_producer=mock_event_producer,
                redis_live=test_valkey_live,
                valkey_stat_client=test_valkey_stat,
            )

        return _create

    @pytest.fixture
    async def user_initial_grace_period_policy(self) -> dict[str, Any]:
        """Policy with user initial grace period"""
        return {"user_initial_grace_period": "100"}

    @pytest.fixture
    async def grace_period_checker(
        self, test_valkey_live: AsyncMock, user_initial_grace_period_policy: dict[str, Any]
    ) -> NewUserGracePeriodChecker:
        """Create and configure NewUserGracePeriodChecker"""
        checker = NewUserGracePeriodChecker(test_valkey_live)
        await checker.populate_config(user_initial_grace_period_policy)
        return checker

    @pytest.fixture
    def kernel_user_joined_data(self, base_time: datetime) -> dict[str, datetime]:
        """Mock kernel table - user table joined data as dict"""
        return {
            "user_created_at": base_time,
        }

    @pytest.mark.asyncio
    async def test_new_user_grace_period(
        self,
        grace_period_checker: NewUserGracePeriodChecker,
        kernel_user_joined_data: dict[str, datetime],
        user_initial_grace_period_policy: dict[str, Any],
    ) -> None:
        """Test new user grace period calculation"""
        # When
        grace_period_end = await grace_period_checker.get_grace_period_end(kernel_user_joined_data)

        # Then
        expected_grace_period_end = kernel_user_joined_data["user_created_at"] + timedelta(
            seconds=float(user_initial_grace_period_policy["user_initial_grace_period"])
        )
        assert grace_period_end == expected_grace_period_end


@dataclass
class _NetworkTimeoutScenario:
    """Test scenario for network timeout without grace period"""

    elapsed_seconds: int
    expected_remaining: float
    idle_timeout: int
    should_alive: bool


@dataclass
class _NetworkTimeoutWithGraceScenario:
    """Test scenario for network timeout with grace period"""

    elapsed_seconds: int
    grace_period_seconds: int
    idle_timeout: int
    expected_remaining: float
    should_alive: bool


class TestNetworkTimeoutIdleChecker:
    @pytest.fixture
    def base_time(self) -> datetime:
        """Reference time for all tests. All other times are calculated as offsets from this."""
        return datetime.now(timezone.utc).replace(microsecond=0)

    @pytest.fixture
    async def test_valkey_live(self) -> AsyncMock:
        """Mock ValkeyLiveClient"""
        mock_client = AsyncMock()
        mock_client.count_active_connections.return_value = 0
        mock_client.get_live_data.return_value = None
        mock_client.get_server_time.return_value = 0.0
        mock_client.store_live_data.return_value = None
        return mock_client

    @pytest.fixture
    async def test_valkey_stat(self) -> AsyncMock:
        """Mock ValkeyStatClient"""
        return AsyncMock()

    @pytest.fixture
    async def mock_event_producer(self) -> AsyncMock:
        """Mock EventProducer"""
        return AsyncMock()

    @pytest.fixture
    async def mock_db_connection(self) -> AsyncMock:
        """Mock database connection"""
        return AsyncMock()

    @pytest.fixture
    def session_id(self) -> SessionId:
        """Session ID for tests"""
        return SessionId(uuid4())

    @pytest.fixture
    def kernel_row(self, session_id: SessionId) -> dict[str, Any]:
        """Kernel row data"""
        return {
            "session_id": session_id,
            "session_type": SessionTypes.INTERACTIVE,
        }

    @pytest.fixture
    def kernel_user_joined_data(self, base_time: datetime) -> dict[str, datetime]:
        """Mock kernel-user joined data"""
        return {
            "user_created_at": base_time,
        }

    @pytest.fixture
    async def network_timeout_checker(
        self,
        scenario: _NetworkTimeoutScenario,
        base_time: datetime,
        test_valkey_live: AsyncMock,
        mock_event_producer: AsyncMock,
        test_valkey_stat: AsyncMock,
        mocker,
    ) -> NetworkTimeoutIdleChecker:
        """Create NetworkTimeoutIdleChecker based on scenario"""
        # Setup time
        now = base_time + timedelta(seconds=scenario.elapsed_seconds)
        test_valkey_live.get_server_time.return_value = now.timestamp()
        mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

        # Create and configure checker
        checker = NetworkTimeoutIdleChecker(
            IdleCheckerArgs(
                event_producer=mock_event_producer,
                redis_live=test_valkey_live,
                valkey_stat_client=test_valkey_stat,
            )
        )
        await checker.populate_config({"threshold": "10"})
        return checker

    @pytest.mark.parametrize(
        "scenario",
        [
            _NetworkTimeoutScenario(
                elapsed_seconds=5, expected_remaining=5.0, idle_timeout=10, should_alive=True
            ),
            _NetworkTimeoutScenario(
                elapsed_seconds=50, expected_remaining=-1, idle_timeout=10, should_alive=False
            ),
        ],
        ids=["positive", "negative"],
    )
    @pytest.mark.asyncio
    async def test_network_timeout_without_grace(
        self,
        scenario: _NetworkTimeoutScenario,
        network_timeout_checker: NetworkTimeoutIdleChecker,
        kernel_row: dict[str, Any],
        session_id: SessionId,
        base_time: datetime,
        test_valkey_live: AsyncMock,
        mock_db_connection: AsyncMock,
    ) -> None:
        """Test network timeout without grace period"""
        # Given
        last_access = base_time
        test_valkey_live.get_live_data.return_value = str(last_access.timestamp()).encode()

        # When
        should_alive = await network_timeout_checker.check_idleness(
            kernel_row,
            mock_db_connection,
            {"idle_timeout": scenario.idle_timeout},
        )

        test_valkey_live.get_live_data.return_value = msgpack.packb(scenario.expected_remaining)
        remaining = await network_timeout_checker.get_checker_result(
            network_timeout_checker._redis_live,
            session_id,
        )

        # Then
        assert should_alive is scenario.should_alive
        assert remaining == scenario.expected_remaining

    @pytest.fixture
    async def network_timeout_checker_with_grace(
        self,
        scenario: _NetworkTimeoutWithGraceScenario,
        base_time: datetime,
        test_valkey_live: AsyncMock,
        mock_event_producer: AsyncMock,
        test_valkey_stat: AsyncMock,
        mocker,
    ) -> NetworkTimeoutIdleChecker:
        """Create NetworkTimeoutIdleChecker based on scenario"""
        # Setup time
        now = base_time + timedelta(seconds=scenario.elapsed_seconds)
        test_valkey_live.get_server_time.return_value = now.timestamp()
        mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

        # Create checker
        checker = NetworkTimeoutIdleChecker(
            IdleCheckerArgs(
                event_producer=mock_event_producer,
                redis_live=test_valkey_live,
                valkey_stat_client=test_valkey_stat,
            )
        )
        await checker.populate_config({"threshold": "10"})
        return checker

    @pytest.fixture
    async def grace_period_checker(
        self,
        scenario: _NetworkTimeoutWithGraceScenario,
        test_valkey_live: AsyncMock,
    ) -> NewUserGracePeriodChecker:
        """Create grace period checker based on scenario"""
        checker = NewUserGracePeriodChecker(test_valkey_live)
        await checker.populate_config({
            "user_initial_grace_period": str(scenario.grace_period_seconds)
        })
        return checker

    @pytest.mark.parametrize(
        "scenario",
        [
            _NetworkTimeoutWithGraceScenario(
                elapsed_seconds=5,
                grace_period_seconds=30,
                idle_timeout=10,
                expected_remaining=35.0,  # Remaining time = (grace_period_end: 30 - now: 5) + idle_timeout(10)
                should_alive=True,
            ),
            _NetworkTimeoutWithGraceScenario(
                elapsed_seconds=50,
                grace_period_seconds=30,
                idle_timeout=10,
                expected_remaining=-1,
                should_alive=False,
            ),
        ],
        ids=["positive", "negative"],
    )
    @pytest.mark.asyncio
    async def test_network_timeout_with_grace(
        self,
        scenario: _NetworkTimeoutWithGraceScenario,
        network_timeout_checker_with_grace: NetworkTimeoutIdleChecker,
        grace_period_checker: NewUserGracePeriodChecker,
        kernel_user_joined_data: dict[str, datetime],
        kernel_row: dict[str, Any],
        session_id: SessionId,
        base_time: datetime,
        test_valkey_live: AsyncMock,
        mock_db_connection: AsyncMock,
    ) -> None:
        """Test network timeout with grace period"""
        # Given
        last_access = base_time
        test_valkey_live.get_live_data.return_value = str(last_access.timestamp()).encode()
        grace_period_end = await grace_period_checker.get_grace_period_end(kernel_user_joined_data)

        # When
        should_alive = await network_timeout_checker_with_grace.check_idleness(
            kernel_row,
            mock_db_connection,
            {"idle_timeout": scenario.idle_timeout},
            grace_period_end=grace_period_end,
        )

        test_valkey_live.get_live_data.return_value = msgpack.packb(scenario.expected_remaining)
        remaining = await network_timeout_checker_with_grace.get_checker_result(
            network_timeout_checker_with_grace._redis_live,
            session_id,
        )

        # Then
        assert should_alive is scenario.should_alive
        assert remaining == scenario.expected_remaining


@pytest.mark.asyncio
async def session_lifetime_checker(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    mocker,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            config_provider_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    # test 1
    # remaining time is positive and no grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 30
    now = datetime(2020, 3, 1, 12, 30, second=10)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    expected = timedelta(seconds=20).total_seconds()
    idle_value = {
        "checkers": {},
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._valkey_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected

    # test 2
    # remaining time is negative and no grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 30
    now = datetime(2020, 3, 1, 12, 30, second=50)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    expected = -1
    idle_value = {
        "checkers": {},
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._valkey_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert not should_alive
    assert remaining == expected

    # test 3
    # remaining time is positive with new user grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=10)
    user_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 10
    now = datetime(2020, 3, 1, 12, 30, second=25)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    grace_period = 30
    expected = timedelta(seconds=15).total_seconds()
    idle_value = {
        "checkers": {
            "user_grace_period": {"user_initial_grace_period": str(grace_period)},
        },
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
        "user_created_at": user_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)
        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            grace_period_end=grace_period_end,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._valkey_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected

    # test 4
    # remaining time is negative with new user grace period
    session_id = SessionId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=40)
    user_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    max_session_lifetime = 10
    now = datetime(2020, 3, 1, 12, 30, second=55)
    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)
    grace_period = 30
    expected = -1
    idle_value = {
        "checkers": {
            "user_grace_period": {"user_initial_grace_period": str(grace_period)},
        },
        "enabled": "",
    }
    kernel = {
        "session_id": session_id,
        "created_at": kernel_created_at,
        "user_created_at": user_created_at,
    }
    policy = {
        "max_session_lifetime": max_session_lifetime,
    }

    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    try:
        await checker_host.start()
        session_lifetime_checker = get_checker_from_host(checker_host, SessionLifetimeChecker)
        grace_period_end = await checker_host._grace_period_checker.get_grace_period_end(kernel)

        should_alive = await session_lifetime_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
            grace_period_end=grace_period_end,
        )
        remaining = await session_lifetime_checker.get_checker_result(
            checker_host._valkey_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert not should_alive
    assert remaining == expected


@pytest.mark.asyncio
async def utilization_idle_checker__utilization(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    mocker,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            config_provider_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    kernel_id = KernelId(uuid4())
    expected = {
        "cpu_util": 10.0,
        "mem": 50.0,
        "cuda_mem": 0.0,
        "cuda_util": 0.0,
    }
    occupied_slots = {
        "mem": 10.0,
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": "0",
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": "100",
            }
        },
        "enabled": "utilization",
    }

    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await checker_host._valkey_stat._client.client.set(str(kernel_id), msgpack.packb(live_stat))
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)
        utilization_idle_checker = cast(UtilizationIdleChecker, utilization_idle_checker)

        utilization = await utilization_idle_checker.get_current_utilization(
            [kernel_id], occupied_slots
        )
    finally:
        await checker_host.shutdown()

    assert utilization == expected


@pytest.mark.asyncio
async def utilization_idle_checker(
    etcd_fixture,
    database_fixture,
    create_app_and_client,
    mocker,
) -> None:
    test_app, _ = await create_app_and_client(
        [
            config_provider_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            background_task_ctx,
            database_ctx,
            distributed_lock_ctx,
        ],
        [".etcd"],
    )
    root_ctx: RootContext = test_app["_root.context"]

    # test 1
    # remaining time is positive and no utilization.
    # - No utilization during initial grace period
    session_id = SessionId(uuid4())
    kernel_id = KernelId(uuid4())
    timewindow = 30
    initial_grace_period = 100
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    now = datetime(2020, 3, 1, 12, 30, second=10)
    expected = timedelta(seconds=120).total_seconds()

    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

    occupied_slots: Mapping[str, Decimal] = {
        "mem": Decimal(10.0),
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }
    kernel = {
        "id": kernel_id,
        "session_id": session_id,
        "created_at": kernel_created_at,
        "cluster_size": 1,
        "occupied_slots": occupied_slots,
    }
    policy = {
        "idle_timeout": timewindow,
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": str(initial_grace_period),
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": str(timewindow),
            }
        },
        "enabled": "utilization",
    }
    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await checker_host._valkey_stat._client.client.set(str(kernel_id), msgpack.packb(live_stat))
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)

        should_alive = await utilization_idle_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
        )
        remaining = await utilization_idle_checker.get_checker_result(
            checker_host._valkey_live, session_id
        )
        util_info = await utilization_idle_checker.get_extra_info(
            checker_host._valkey_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected
    assert util_info is None

    # test 2
    # remaining time is positive with utilization.
    session_id = SessionId(uuid4())
    kernel_id = KernelId(uuid4())
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    now = datetime(2020, 3, 1, 12, 30, second=10)
    initial_grace_period = 0
    timewindow = 15
    expected = timedelta(seconds=5).total_seconds()

    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

    occupied_slots = {
        "mem": Decimal(10.0),
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }
    kernel = {
        "id": kernel_id,
        "session_id": session_id,
        "created_at": kernel_created_at,
        "cluster_size": 1,
        "occupied_slots": occupied_slots,
    }
    policy = {
        "idle_timeout": timewindow,
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": str(initial_grace_period),
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": str(timewindow),
            }
        },
        "enabled": "utilization",
    }
    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await checker_host._valkey_stat._client.client.set(str(kernel_id), msgpack.packb(live_stat))
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)

        should_alive = await utilization_idle_checker.check_idleness(
            kernel, checker_host._db, policy
        )
        remaining = await utilization_idle_checker.get_checker_result(
            checker_host._valkey_live, session_id
        )
        util_info = await utilization_idle_checker.get_extra_info(
            checker_host._valkey_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected
    assert util_info is not None

    # test 3
    # remaining time is negative with utilization.
    session_id = SessionId(uuid4())
    kernel_id = KernelId(uuid4())
    timewindow = 15
    initial_grace_period = 0
    kernel_created_at = datetime(2020, 3, 1, 12, 30, second=0)
    now = datetime(2020, 3, 1, 12, 30, second=50)
    expected = -1

    mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

    occupied_slots = {
        "mem": Decimal(10.0),
    }
    live_stat = {
        "mem": {
            "current": "5.0",
            "pct": "10.0",
        },
        "cpu_util": {
            "pct": "10.0",
        },
    }
    kernel = {
        "id": kernel_id,
        "session_id": session_id,
        "created_at": kernel_created_at,
        "cluster_size": 1,
        "occupied_slots": occupied_slots,
    }
    policy = {
        "idle_timeout": timewindow,
    }

    resource_thresholds = {
        "cpu_util": {"average": "0"},
        "mem": {"average": "0"},
        "cuda_util": {"average": "0"},
        "cuda_mem": {"average": "0"},
    }
    idle_value = {
        "checkers": {
            "utilization": {
                "initial-grace-period": str(initial_grace_period),
                "resource-thresholds": resource_thresholds,
                "thresholds-check-operator": "or",
                "time-window": str(timewindow),
            }
        },
        "enabled": "utilization",
    }
    await root_ctx.etcd.put_prefix("config/idle", idle_value)  # type: ignore[arg-type]
    checker_host = await init_idle_checkers(
        root_ctx.db,
        root_ctx.config_provider,
        root_ctx.event_producer,
        root_ctx.distributed_lock_factory,
    )
    await checker_host._valkey_stat._client.client.set(str(kernel_id), msgpack.packb(live_stat))
    try:
        await checker_host.start()
        utilization_idle_checker = get_checker_from_host(checker_host, UtilizationIdleChecker)

        should_alive = await utilization_idle_checker.check_idleness(
            kernel,
            checker_host._db,
            policy,
        )
        remaining = await utilization_idle_checker.get_checker_result(
            checker_host._valkey_live, session_id
        )
        util_info = await utilization_idle_checker.get_extra_info(
            checker_host._valkey_live, session_id
        )
    finally:
        await checker_host.shutdown()

    assert should_alive
    assert remaining == expected
    assert util_info is not None
