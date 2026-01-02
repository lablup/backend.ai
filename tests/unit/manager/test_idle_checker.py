from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ai.backend.common import msgpack
from ai.backend.common.types import KernelId, SessionId, SessionTypes
from ai.backend.manager.idle import (
    IdleCheckerArgs,
    NetworkTimeoutIdleChecker,
    NewUserGracePeriodChecker,
    SessionLifetimeChecker,
    UtilizationIdleChecker,
    calculate_remaining_time,
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
        # Test 1: No grace period
        # remaining = (idle_baseline - now) + timeout_period
        # = (12:30:00 - 12:30:20) + 30s = -20s + 30s = 10s
        _RemainingTimeCalculationTestConfig(
            now=datetime(2020, 3, 1, 12, 30, second=20),
            idle_baseline=datetime(2020, 3, 1, 12, 30, second=0),
            timeout_period=timedelta(seconds=30),
            grace_period_end=None,
            expected_remaining=10.0,
        ),
        # Test 2: Grace period takes precedence (grace_period_end > idle_baseline)
        # baseline = max(idle_baseline, grace_period_end) = max(12:30:00, 12:30:30) = 12:30:30
        # remaining = (baseline - now) + timeout_period
        # = (12:30:30 - 12:30:20) + 30s = 10s + 30s = 40s
        _RemainingTimeCalculationTestConfig(
            now=datetime(2020, 3, 1, 12, 30, second=20),
            idle_baseline=datetime(2020, 3, 1, 12, 30, second=0),
            timeout_period=timedelta(seconds=30),
            grace_period_end=datetime(2020, 3, 1, 12, 30, second=30),
            expected_remaining=40.0,
        ),
        # Test 3: idle_baseline takes precedence (idle_baseline > grace_period_end)
        # baseline = max(idle_baseline, grace_period_end) = max(12:30:30, 12:30:20) = 12:30:30
        # remaining = (baseline - now) + timeout_period
        # = (12:30:30 - 12:30:20) + 30s = 10s + 30s = 40s
        _RemainingTimeCalculationTestConfig(
            now=datetime(2020, 3, 1, 12, 30, second=20),
            idle_baseline=datetime(2020, 3, 1, 12, 30, second=30),
            timeout_period=timedelta(seconds=30),
            grace_period_end=datetime(2020, 3, 1, 12, 30, second=20),
            expected_remaining=40.0,
        ),
        # Test 4: Timeout exceeded (negative remaining time)
        # baseline = max(idle_baseline, grace_period_end) = max(12:30:00, 12:30:10) = 12:30:10
        # remaining = (baseline - now) + timeout_period
        # = (12:30:10 - 12:30:50) + 10s = -40s + 10s = -30s
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
async def test_remaining_time_calculation(
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
    async def valkey_live(self) -> AsyncMock:
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
    async def user_initial_grace_period_policy(self) -> dict[str, Any]:
        """Policy with user initial grace period"""
        return {"user_initial_grace_period": "100"}

    @pytest.fixture
    async def grace_period_checker(
        self, valkey_live: AsyncMock, user_initial_grace_period_policy: dict[str, Any]
    ) -> NewUserGracePeriodChecker:
        """Create and configure NewUserGracePeriodChecker"""
        checker = NewUserGracePeriodChecker(valkey_live)
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


@dataclass
class _SessionLifetimeTestConfig:
    """Configuration for session lifetime test cases"""

    elapsed_seconds: int  # Time elapsed since session creation
    max_lifetime_seconds: int  # Max session lifetime policy
    expected_remaining: float  # Expected remaining time (-1 if timeout)
    expected_alive: bool  # Expected should_alive result
    user_initial_grace_period: int = 0  # User initial grace period (default: 0)


class TestSessionLifetimeChecker:
    @pytest.fixture
    def base_time(self) -> datetime:
        """Reference time: All sessions and users created at this time"""
        return datetime.now(timezone.utc).replace(microsecond=0)

    @pytest.fixture
    async def valkey_live(self) -> AsyncMock:
        """Mock ValkeyLiveClient - configure return values in scenario fixtures"""
        mock_client = AsyncMock()
        mock_client.count_active_connections.return_value = 0
        mock_client.get_live_data.return_value = None
        mock_client.get_server_time.return_value = 0.0
        mock_client.store_live_data.return_value = None
        return mock_client

    @pytest.fixture
    async def valkey_stat(self) -> AsyncMock:
        """Mock ValkeyStatClient"""
        return AsyncMock()

    @pytest.fixture
    async def event_producer(self) -> AsyncMock:
        """Mock EventProducer"""
        return AsyncMock()

    @pytest.fixture
    async def db_connection(self) -> AsyncMock:
        """Mock database connection"""
        return AsyncMock()

    @pytest.fixture
    def session_id(self) -> SessionId:
        """Session ID for tests"""
        return SessionId(uuid4())

    @pytest.fixture
    def kernel_user_joined_data(self, base_time: datetime) -> dict[str, datetime]:
        """Kernel user joined data with user created at base_time"""
        return {"user_created_at": base_time}

    @pytest.fixture
    async def grace_period_checker(
        self,
        valkey_live: AsyncMock,
        test_config: _SessionLifetimeTestConfig,
    ) -> NewUserGracePeriodChecker:
        """NewUserGracePeriodChecker with 30s grace period"""
        checker = NewUserGracePeriodChecker(valkey_live)
        await checker.populate_config({
            "user_initial_grace_period": test_config.user_initial_grace_period
        })
        return checker

    @pytest.fixture
    def session_kernel_row(self, session_id: SessionId, base_time: datetime) -> dict[str, Any]:
        """Kernel row with session created at base_time"""
        return {
            "session_id": session_id,
            "created_at": base_time,
        }

    @pytest.fixture
    def session_lifetime_policy(self, test_config: _SessionLifetimeTestConfig) -> dict[str, Any]:
        """Policy with max_session_lifetime from test_config"""
        return {"max_session_lifetime": test_config.max_lifetime_seconds}

    @pytest.fixture
    async def session_lifetime_checker(
        self,
        test_config: _SessionLifetimeTestConfig,
        base_time: datetime,
        valkey_live: AsyncMock,
        valkey_stat: AsyncMock,
        event_producer: AsyncMock,
        mocker,
    ) -> SessionLifetimeChecker:
        """SessionLifetimeChecker with time configured based on test_config"""
        # Setup time: session created at base_time, current time = base_time + elapsed
        now = base_time + timedelta(seconds=test_config.elapsed_seconds)
        valkey_live.get_server_time.return_value = now.timestamp()
        mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

        # Create and configure checker
        checker = SessionLifetimeChecker(
            IdleCheckerArgs(
                event_producer=event_producer,
                redis_live=valkey_live,
                valkey_stat_client=valkey_stat,
            )
        )
        await checker.populate_config({})
        return checker

    @pytest.mark.parametrize(
        "test_config",
        [
            # Remaining = max_lifetime - elapsed = 30 - 10 = 20s
            _SessionLifetimeTestConfig(
                elapsed_seconds=10,
                max_lifetime_seconds=30,
                expected_remaining=20.0,
                expected_alive=True,
            ),
            # Timeout exceeded: elapsed (50s) > max_lifetime (30s)
            _SessionLifetimeTestConfig(
                elapsed_seconds=50,
                max_lifetime_seconds=30,
                expected_remaining=-1,
                expected_alive=False,
            ),
        ],
        ids=["positive_20s_remaining", "negative_timeout_exceeded"],
    )
    @pytest.mark.asyncio
    async def test_session_lifetime_without_grace(
        self,
        test_config: _SessionLifetimeTestConfig,
        session_id: SessionId,
        valkey_live: AsyncMock,
        db_connection: AsyncMock,
        session_lifetime_checker: SessionLifetimeChecker,
        session_kernel_row: dict[str, Any],
        session_lifetime_policy: dict[str, Any],
    ) -> None:
        """Test session lifetime without grace period"""
        # When - check_idleness runs and stores remaining time
        should_alive = await session_lifetime_checker.check_idleness(
            session_kernel_row,
            db_connection,
            session_lifetime_policy,
        )

        # Mock: get_checker_result will read the stored result
        valkey_live.get_live_data.return_value = msgpack.packb(test_config.expected_remaining)
        remaining = await session_lifetime_checker.get_checker_result(
            session_lifetime_checker._redis_live, session_id
        )

        # Then
        assert should_alive is test_config.expected_alive
        assert remaining == test_config.expected_remaining

    @pytest.mark.parametrize(
        "test_config",
        [
            # Grace period (30s) not exceeded
            # remaining = (grace_end + max_lifetime) - now = (30+10) - 25 = 15s
            _SessionLifetimeTestConfig(
                elapsed_seconds=25,
                max_lifetime_seconds=10,
                expected_remaining=15.0,
                expected_alive=True,
                user_initial_grace_period=30,
            ),
            # Grace period + max_lifetime exceeded
            # timeout_deadline = grace_end + max_lifetime = 30 + 10 = 40s, now = 45s
            _SessionLifetimeTestConfig(
                elapsed_seconds=45,
                max_lifetime_seconds=10,
                expected_remaining=-1,
                expected_alive=False,
                user_initial_grace_period=30,
            ),
        ],
        ids=["grace_positive_15s_remaining", "grace_negative_exceeded"],
    )
    @pytest.mark.asyncio
    async def test_session_lifetime_with_grace(
        self,
        test_config: _SessionLifetimeTestConfig,
        session_id: SessionId,
        valkey_live: AsyncMock,
        db_connection: AsyncMock,
        session_lifetime_checker: SessionLifetimeChecker,
        session_kernel_row: dict[str, Any],
        session_lifetime_policy: dict[str, Any],
        grace_period_checker: NewUserGracePeriodChecker,
        kernel_user_joined_data: dict[str, datetime],
    ) -> None:
        # Get grace period end (user_created_at = base_time, grace from test_config)
        grace_period_end = await grace_period_checker.get_grace_period_end(kernel_user_joined_data)

        # When - check_idleness runs with grace_period_end
        should_alive = await session_lifetime_checker.check_idleness(
            session_kernel_row,
            db_connection,
            session_lifetime_policy,
            grace_period_end=grace_period_end,
        )

        # Mock: get_checker_result will read the stored result
        valkey_live.get_live_data.return_value = msgpack.packb(test_config.expected_remaining)
        remaining = await session_lifetime_checker.get_checker_result(
            session_lifetime_checker._redis_live, session_id
        )

        # Then
        assert should_alive is test_config.expected_alive
        assert remaining == test_config.expected_remaining


@dataclass
class _UtilizationCurrentTestConfig:
    """Configuration for get_current_utilization test"""

    mem_current: float  # Current memory usage (GB)
    mem_pct: float  # Memory percentage
    cpu_util_pct: float  # CPU utilization percentage
    mem_slots: Decimal  # Total memory slots (GB)
    expected_cpu_util: float  # Expected CPU utilization
    expected_mem_util: float  # Expected memory utilization


@dataclass
class _UtilizationGracePeriodTestConfig:
    """Configuration for utilization idle test during grace period"""

    elapsed_seconds: int  # Time elapsed since kernel creation
    initial_grace_period_seconds: int  # Initial grace period
    time_window_seconds: int  # Time window for idle check (policy.idle_timeout)
    mem_current: float  # Current memory usage (GB)
    mem_pct: float  # Memory percentage
    cpu_util_pct: float  # CPU utilization percentage
    threshold_cpu: float  # Required CPU threshold
    threshold_mem: float  # Required memory threshold
    expected_remaining: float  # Expected remaining time
    expected_alive: bool  # Expected should_alive result


@dataclass
class _UtilizationIdleTestConfig:
    """Configuration for utilization idle test cases after grace period"""

    elapsed_seconds: int  # Time elapsed since kernel creation
    time_window_seconds: int  # Time window for idle check
    expected_remaining: float  # Expected remaining time
    expected_alive: bool  # Expected should_alive result


@dataclass
class _UtilizationInsufficientTestConfig:
    """Configuration for insufficient utilization test

    Tests when utilization is below thresholds after grace period ends.
    The checker uses OR operator by default, so if any resource (CPU or mem)
    exceeds its threshold, should_alive=True. If all resources are below
    thresholds, should_alive=False.
    """

    elapsed_seconds: int  # Time elapsed since kernel creation
    time_window_seconds: int  # Time window for idle check
    mem_current: float  # Current memory usage (GB)
    mem_pct: float  # Memory percentage
    cpu_util_pct: float  # CPU utilization percentage
    threshold_cpu: float  # Required CPU threshold (%)
    threshold_mem: float  # Required memory threshold (%)
    expected_remaining: float  # Expected remaining time
    expected_alive: bool  # Expected should_alive result


class TestUtilizationIdleChecker:
    """Test suite for UtilizationIdleChecker

    Tests the following scenarios:
    1. test_utilization_current: Get current utilization (CPU and memory)
    2. test_utilization_checker_with_grace_period: Grace period behavior
       - Within grace period with high/low utilization
       - Timeout exceeded with high/low utilization
    3. test_utilization_sufficient: Sufficient utilization (no grace period)
       - Session should NOT terminate when utilization exceeds thresholds
    4. test_utilization_insufficient: Insufficient utilization (no grace period)
       - Session should terminate when utilization is below thresholds
    """

    @pytest.fixture
    def base_time(self) -> datetime:
        """Reference time for all tests. All other times are calculated as offsets from this."""
        return datetime.now(timezone.utc).replace(microsecond=0)

    @pytest.fixture
    async def valkey_live(self) -> AsyncMock:
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
    async def valkey_stat(self) -> AsyncMock:
        """Mock ValkeyStatClient - configure return values in scenario fixtures"""
        return AsyncMock()

    @pytest.fixture
    async def event_producer(self) -> AsyncMock:
        """Mock EventProducer"""
        return AsyncMock()

    @pytest.fixture
    async def db_connection(self) -> AsyncMock:
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

    # Test 1: Get current utilization
    @pytest.fixture
    def utilization_kernel_id(self) -> KernelId:
        """Kernel ID for utilization tests"""
        return KernelId(uuid4())

    @pytest.fixture
    async def utilization_current_checker(
        self,
        current_test_config: _UtilizationCurrentTestConfig,
        valkey_live: AsyncMock,
        valkey_stat: AsyncMock,
        event_producer: AsyncMock,
    ) -> UtilizationIdleChecker:
        """UtilizationIdleChecker for getting current utilization"""
        # Configure mock return values from test_config
        live_stat = {
            "mem": {
                "current": str(current_test_config.mem_current),
                "pct": str(current_test_config.mem_pct),
            },
            "cpu_util": {
                "pct": str(current_test_config.cpu_util_pct),
            },
        }
        valkey_stat.get_kernel_statistics.return_value = live_stat

        # Create and configure checker
        checker = UtilizationIdleChecker(
            IdleCheckerArgs(
                event_producer=event_producer,
                redis_live=valkey_live,
                valkey_stat_client=valkey_stat,
            )
        )
        await checker.populate_config({
            "initial-grace-period": "0",
            "resource-thresholds": {
                "cpu_util": {"average": "0"},
                "mem": {"average": "0"},
                "cuda_util": {"average": "0"},
                "cuda_mem": {"average": "0"},
            },
            "thresholds-check-operator": "or",
            "time-window": "100",
        })
        return checker

    @pytest.mark.parametrize(
        "current_test_config",
        [
            # mem = mem.pct + (mem.current / mem_slots * 100) = 10.0 + (6.0 / 10.0 * 100) = 70.0
            # cpu = cpu_util.pct = 10.0
            _UtilizationCurrentTestConfig(
                mem_current=6.0,
                mem_pct=10.0,
                cpu_util_pct=10.0,
                mem_slots=Decimal(10.0),
                expected_cpu_util=10.0,
                expected_mem_util=70.0,
            ),
            # mem = 5.0 + (2.0 / 10.0 * 100) = 25.0
            # cpu = cpu_util.pct = 85.0
            _UtilizationCurrentTestConfig(
                mem_current=2.0,
                mem_pct=5.0,
                cpu_util_pct=85.0,
                mem_slots=Decimal(10.0),
                expected_cpu_util=85.0,
                expected_mem_util=25.0,
            ),
        ],
        ids=["mem_70pct_cpu_10pct", "mem_25pct_cpu_85pct"],
    )
    @pytest.mark.asyncio
    async def test_utilization_current(
        self,
        current_test_config: _UtilizationCurrentTestConfig,
        utilization_current_checker: UtilizationIdleChecker,
        utilization_kernel_id: KernelId,
    ) -> None:
        """Test getting current utilization"""
        # Given
        memory_slots = {"mem": current_test_config.mem_slots}
        expected_utilization = {
            "cpu_util": current_test_config.expected_cpu_util,
            "mem": current_test_config.expected_mem_util,
            "cuda_mem": 0.0,
            "cuda_util": 0.0,
        }

        # When
        utilization = await utilization_current_checker.get_current_utilization(
            [utilization_kernel_id],
            memory_slots,
        )

        # Then
        assert utilization == expected_utilization

    # Test 2: Grace period test
    @pytest.fixture
    async def utilization_grace_period_checker(
        self,
        grace_test_config: _UtilizationGracePeriodTestConfig,
        base_time: datetime,
        session_id: SessionId,
        valkey_live: AsyncMock,
        valkey_stat: AsyncMock,
        event_producer: AsyncMock,
        mocker,
    ) -> UtilizationIdleChecker:
        """UtilizationIdleChecker configured based on grace_test_config"""
        # Time setup: elapsed time since kernel created
        now = base_time + timedelta(seconds=grace_test_config.elapsed_seconds)
        valkey_live.get_server_time.return_value = now.timestamp()
        mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

        # Configure stat return values from test_config
        live_stat = {
            "mem": {
                "current": str(grace_test_config.mem_current),
                "pct": str(grace_test_config.mem_pct),
            },
            "cpu_util": {
                "pct": str(grace_test_config.cpu_util_pct),
            },
        }
        valkey_stat.get_kernel_statistics.return_value = live_stat

        # Mock util_first_collected to simulate that samples have been collected
        # Set it to time_window seconds ago so do_idle_check becomes True
        util_first_collected = now.timestamp() - grace_test_config.time_window_seconds

        async def get_live_data_side_effect(key: str):
            if key.endswith(".util_first_collected"):
                return str(util_first_collected).encode()
            if key.endswith(".util_last_collected"):
                # Return a timestamp in the past to pass the interval check
                return str(util_first_collected).encode()
            if key.endswith(".util_series"):
                # Return None to start with empty series
                return None
            return None

        valkey_live.get_live_data.side_effect = get_live_data_side_effect

        # Create and configure checker with grace period and thresholds from test_config
        checker = UtilizationIdleChecker(
            IdleCheckerArgs(
                event_producer=event_producer,
                redis_live=valkey_live,
                valkey_stat_client=valkey_stat,
            )
        )
        await checker.populate_config({
            "initial-grace-period": str(grace_test_config.initial_grace_period_seconds),
            "resource-thresholds": {
                "cpu_util": {"average": str(grace_test_config.threshold_cpu)},
                "mem": {"average": str(grace_test_config.threshold_mem)},
                "cuda_util": {"average": "0"},
                "cuda_mem": {"average": "0"},
            },
            "thresholds-check-operator": "or",
            "time-window": str(grace_test_config.time_window_seconds),
        })
        return checker

    @pytest.mark.parametrize(
        "grace_test_config",
        [
            # Case 1: Within grace period, high utilization
            # Remaining = (grace + window) - elapsed = (100 + 30) - 10 = 120s
            # High utilization (70% mem, 10% cpu) exceeds thresholds (0%) -> should_alive=True
            _UtilizationGracePeriodTestConfig(
                elapsed_seconds=10,
                initial_grace_period_seconds=100,
                time_window_seconds=30,
                mem_current=5.0,
                mem_pct=10.0,
                cpu_util_pct=10.0,
                threshold_cpu=0.0,
                threshold_mem=0.0,
                expected_remaining=120.0,
                expected_alive=True,
            ),
            # Case 2: Timeout exceeded AND low utilization -> should terminate
            # elapsed (150) > grace + window (130), low utilization (6% mem, 5% cpu) < thresholds (50%)
            _UtilizationGracePeriodTestConfig(
                elapsed_seconds=150,
                initial_grace_period_seconds=100,
                time_window_seconds=30,
                mem_current=1.0,
                mem_pct=5.0,
                cpu_util_pct=5.0,
                threshold_cpu=50.0,
                threshold_mem=50.0,
                expected_remaining=-1,
                expected_alive=False,
            ),
            # Case 3: Timeout exceeded BUT high utilization -> should NOT terminate
            # elapsed (150) > grace + window (130), high utilization (70% mem, 10% cpu) exceeds thresholds (0%)
            _UtilizationGracePeriodTestConfig(
                elapsed_seconds=150,
                initial_grace_period_seconds=100,
                time_window_seconds=30,
                mem_current=5.0,
                mem_pct=10.0,
                cpu_util_pct=10.0,
                threshold_cpu=0.0,
                threshold_mem=0.0,
                expected_remaining=-1,
                expected_alive=True,
            ),
            # Case 4: Within grace period BUT low utilization -> should NOT terminate (grace period protection)
            # elapsed (10) < grace (100), low utilization (6% mem, 5% cpu) < thresholds (50%)
            # During grace period, checker returns True regardless of utilization (line 1089-1090 in idle.py)
            _UtilizationGracePeriodTestConfig(
                elapsed_seconds=10,
                initial_grace_period_seconds=100,
                time_window_seconds=30,
                mem_current=1.0,
                mem_pct=5.0,
                cpu_util_pct=5.0,
                threshold_cpu=50.0,
                threshold_mem=50.0,
                expected_remaining=120.0,
                expected_alive=True,
            ),
        ],
        ids=[
            "within_grace_high_util",
            "timeout_low_util",
            "timeout_high_util",
            "within_grace_low_util",
        ],
    )
    @pytest.mark.asyncio
    async def test_utilization_checker_with_grace_period(
        self,
        grace_test_config: _UtilizationGracePeriodTestConfig,
        utilization_grace_period_checker: UtilizationIdleChecker,
        utilization_kernel_row: dict[str, Any],
        session_id: SessionId,
        valkey_live: AsyncMock,
        db_connection: AsyncMock,
    ) -> None:
        """Test utilization during grace period (util_info should be None)"""
        # When - check_idleness runs and stores remaining time
        should_alive = await utilization_grace_period_checker.check_idleness(
            utilization_kernel_row,
            db_connection,
            {"idle_timeout": grace_test_config.time_window_seconds},
        )

        # Reset side_effect after check_idleness so return_value can be used
        valkey_live.get_live_data.side_effect = None

        # Mock: get_checker_result
        valkey_live.get_live_data.return_value = msgpack.packb(grace_test_config.expected_remaining)
        remaining = await utilization_grace_period_checker.get_checker_result(
            utilization_grace_period_checker._redis_live,
            session_id,
        )

        # Mock: get_extra_info (None during grace period)
        valkey_live.get_live_data.return_value = None
        util_info = await utilization_grace_period_checker.get_extra_info(
            utilization_grace_period_checker._redis_live,
            session_id,
        )

        # Then
        assert should_alive is grace_test_config.expected_alive
        assert remaining == grace_test_config.expected_remaining
        assert util_info is None

    # Test 3: Sufficient utilization (no grace period, high utilization)
    @pytest.fixture
    async def utilization_idle_checker(
        self,
        test_config: _UtilizationIdleTestConfig,
        base_time: datetime,
        valkey_live: AsyncMock,
        valkey_stat: AsyncMock,
        event_producer: AsyncMock,
        mocker,
    ) -> UtilizationIdleChecker:
        """UtilizationIdleChecker configured based on test_config"""
        # Time setup: elapsed time since kernel created
        now = base_time + timedelta(seconds=test_config.elapsed_seconds)
        valkey_live.get_server_time.return_value = now.timestamp()
        mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

        # Configure stat return values
        live_stat = {
            "mem": {"current": "5.0", "pct": "10.0"},
            "cpu_util": {"pct": "10.0"},
        }
        valkey_stat.get_kernel_statistics.return_value = live_stat

        # Create and configure checker (no grace period)
        checker = UtilizationIdleChecker(
            IdleCheckerArgs(
                event_producer=event_producer,
                redis_live=valkey_live,
                valkey_stat_client=valkey_stat,
            )
        )
        await checker.populate_config({
            "initial-grace-period": "0",
            "resource-thresholds": {
                "cpu_util": {"average": "0"},
                "mem": {"average": "0"},
                "cuda_util": {"average": "0"},
                "cuda_mem": {"average": "0"},
            },
            "thresholds-check-operator": "or",
            "time-window": str(test_config.time_window_seconds),
        })
        return checker

    @pytest.mark.parametrize(
        "test_config",
        [
            # Positive remaining: remaining = window - elapsed = 15 - 5 = 10s
            _UtilizationIdleTestConfig(
                elapsed_seconds=5,
                time_window_seconds=15,
                expected_remaining=10.0,
                expected_alive=True,
            ),
            # Negative remaining: timeout exceeded, but alive due to utilization
            _UtilizationIdleTestConfig(
                elapsed_seconds=50,
                time_window_seconds=15,
                expected_remaining=-1,
                expected_alive=True,
            ),
        ],
        ids=["positive_10s", "negative_alive_utilization"],
    )
    @pytest.mark.asyncio
    async def test_utilization_sufficient_without_grace_period(
        self,
        test_config: _UtilizationIdleTestConfig,
        utilization_idle_checker: UtilizationIdleChecker,
        utilization_kernel_row: dict[str, Any],
        session_id: SessionId,
        valkey_live: AsyncMock,
        db_connection: AsyncMock,
    ) -> None:
        """Test utilization with sufficient usage (should NOT terminate session)"""
        # When - check_idleness runs and stores remaining time
        should_alive = await utilization_idle_checker.check_idleness(
            utilization_kernel_row,
            db_connection,
            {"idle_timeout": test_config.time_window_seconds},
        )

        # Mock: get_checker_result
        valkey_live.get_live_data.return_value = msgpack.packb(test_config.expected_remaining)
        remaining = await utilization_idle_checker.get_checker_result(
            utilization_idle_checker._redis_live,
            session_id,
        )

        # Mock: get_extra_info (not None after grace period)
        valkey_live.get_live_data.return_value = msgpack.packb({"resources": {}})
        util_info = await utilization_idle_checker.get_extra_info(
            utilization_idle_checker._redis_live,
            session_id,
        )

        # Then
        assert should_alive is test_config.expected_alive
        assert remaining == test_config.expected_remaining
        assert util_info is not None

    # Shared fixture for utilization idle check tests
    @pytest.fixture
    def ten_gb_memory_slots(self) -> dict[str, Decimal]:
        """Resource slots with 10GB memory"""
        return {"mem": Decimal(10.0)}

    @pytest.fixture
    def utilization_kernel_row(
        self,
        session_id: SessionId,
        utilization_kernel_id: KernelId,
        ten_gb_memory_slots: dict[str, Decimal],
        base_time: datetime,
    ) -> dict[str, Any]:
        """Kernel row for utilization tests"""
        return {
            "id": utilization_kernel_id,
            "session_id": session_id,
            "created_at": base_time,
            "cluster_size": 1,
            "occupied_slots": ten_gb_memory_slots,
            "requested_slots": ten_gb_memory_slots,
        }

    # Test 4: Insufficient utilization (session should be terminated)
    @pytest.fixture
    async def utilization_insufficient_checker(
        self,
        insufficient_test_config: _UtilizationInsufficientTestConfig,
        base_time: datetime,
        valkey_live: AsyncMock,
        valkey_stat: AsyncMock,
        event_producer: AsyncMock,
        mocker,
    ) -> UtilizationIdleChecker:
        """UtilizationIdleChecker configured based on insufficient_test_config"""
        # Time setup: elapsed time since kernel created
        now = base_time + timedelta(seconds=insufficient_test_config.elapsed_seconds)
        valkey_live.get_server_time.return_value = now.timestamp()
        mocker.patch("ai.backend.manager.idle.get_db_now", return_value=now)

        # Configure stat return values from test_config
        live_stat = {
            "mem": {
                "current": str(insufficient_test_config.mem_current),
                "pct": str(insufficient_test_config.mem_pct),
            },
            "cpu_util": {"pct": str(insufficient_test_config.cpu_util_pct)},
        }
        valkey_stat.get_kernel_statistics.return_value = live_stat

        # Create and configure checker with thresholds from test_config
        checker = UtilizationIdleChecker(
            IdleCheckerArgs(
                event_producer=event_producer,
                redis_live=valkey_live,
                valkey_stat_client=valkey_stat,
            )
        )
        await checker.populate_config({
            "initial-grace-period": "0",
            "resource-thresholds": {
                "cpu_util": {"average": str(insufficient_test_config.threshold_cpu)},
                "mem": {"average": str(insufficient_test_config.threshold_mem)},
                "cuda_util": {"average": "0"},
                "cuda_mem": {"average": "0"},
            },
            "thresholds-check-operator": "or",
            "time-window": str(insufficient_test_config.time_window_seconds),
        })
        return checker

    @pytest.mark.parametrize(
        "insufficient_test_config",
        [
            # Low utilization (5%) < high threshold (50%), timeout exceeded
            _UtilizationInsufficientTestConfig(
                elapsed_seconds=50,
                time_window_seconds=15,
                mem_current=1.0,
                mem_pct=5.0,
                cpu_util_pct=5.0,
                threshold_cpu=50.0,
                threshold_mem=50.0,
                expected_remaining=-1,
                expected_alive=False,
            ),
        ],
        ids=["low_util_5pct_threshold_50pct"],
    )
    @pytest.mark.asyncio
    async def test_utilization_insufficient_without_grace_period(
        self,
        insufficient_test_config: _UtilizationInsufficientTestConfig,
        utilization_insufficient_checker: UtilizationIdleChecker,
        utilization_kernel_row: dict[str, Any],
        session_id: SessionId,
        base_time: datetime,
        valkey_live: AsyncMock,
        db_connection: AsyncMock,
    ) -> None:
        """Test utilization with insufficient usage below thresholds (should terminate session)"""
        # Given
        util_first_collected_time = base_time.timestamp()

        # Setup side_effect using key inspection
        def mock_get_live_data_side_effect(key: str) -> Optional[bytes]:
            if ".util_first_collected" in key:
                return f"{util_first_collected_time:.06f}".encode()
            elif ".util_series" in key:
                return msgpack.packb({"cpu_util": [], "mem": [], "cuda_util": [], "cuda_mem": []})
            elif ".utilization_extra" in key:
                return msgpack.packb({"resources": {}})
            elif ".utilization" in key:
                return msgpack.packb(insufficient_test_config.expected_remaining)
            return None

        valkey_live.get_live_data.side_effect = mock_get_live_data_side_effect

        # When - check_idleness runs and stores remaining time
        should_alive = await utilization_insufficient_checker.check_idleness(
            utilization_kernel_row,
            db_connection,
            {"idle_timeout": insufficient_test_config.time_window_seconds},
        )

        # get_checker_result will read the stored result (already mocked above)
        remaining = await utilization_insufficient_checker.get_checker_result(
            utilization_insufficient_checker._redis_live,
            session_id,
        )

        # get_extra_info will read utilization extra info (already mocked above)
        util_info = await utilization_insufficient_checker.get_extra_info(
            utilization_insufficient_checker._redis_live,
            session_id,
        )

        # Then
        assert should_alive is insufficient_test_config.expected_alive
        assert remaining == insufficient_test_config.expected_remaining
        assert util_info is not None
