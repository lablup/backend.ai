import asyncio
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.proxy.backend.http import HTTPBackend
from ai.backend.appproxy.worker.types import RootContext
from ai.backend.common.types import ModelServiceStatus


@pytest.fixture
async def mock_root_context():
    """Mock RootContext for testing."""
    context = Mock(spec=RootContext)
    context.last_used_time_marker_redis_queue = AsyncMock()
    context.request_counter_redis_queue = AsyncMock()
    context.metrics = Mock()
    context.metrics.proxy = Mock()
    context.metrics.proxy.observe_upstream_http_request = Mock()
    context.metrics.proxy.observe_upstream_http_response = Mock()
    context.local_config = Mock()
    context.local_config.proxy_worker = Mock()
    context.local_config.proxy_worker.tls_advertised = False
    context.local_config.proxy_worker.tls_listen = False
    return context


@pytest.fixture
def mock_circuit():
    """Mock circuit for testing."""
    circuit = Mock()
    circuit.id = uuid4()
    circuit.app = "test-app"
    return circuit


@pytest.fixture
def sample_routes():
    """Sample routes for testing."""
    return [
        RouteInfo(
            route_id=uuid4(),
            session_id=uuid4(),
            session_name="session1",
            kernel_host="localhost",
            kernel_port=8001,
            protocol=ProxyProtocol.HTTP,
            traffic_ratio=1.0,
            last_health_check=0,
            consecutive_failures=0,
            health_status=ModelServiceStatus.HEALTHY,
        ),
        RouteInfo(
            route_id=uuid4(),
            session_id=uuid4(),
            session_name="session2",
            kernel_host="localhost",
            kernel_port=8002,
            protocol=ProxyProtocol.HTTP,
            traffic_ratio=1.0,
            last_health_check=0,
            consecutive_failures=0,
            health_status=ModelServiceStatus.HEALTHY,
        ),
    ]


@pytest.fixture
async def http_backend(mock_root_context, mock_circuit, sample_routes):
    """HTTPBackend instance for testing."""
    return HTTPBackend(sample_routes, mock_root_context, mock_circuit)


@pytest.mark.asyncio
async def test_update_routes_add_new_routes(http_backend, sample_routes):
    """Test adding new routes to HTTPBackend."""
    # Create new routes with different route_ids
    new_route = RouteInfo(
        route_id=uuid4(),
        session_id=uuid4(),
        session_name="session3",
        kernel_host="localhost",
        kernel_port=8003,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=1.0,
        last_health_check=0,
        consecutive_failures=0,
        health_status=ModelServiceStatus.HEALTHY,
    )
    new_routes = sample_routes + [new_route]

    # Verify initial state
    assert len(http_backend.client_sessions) == 2
    initial_session_ids = set(http_backend.client_sessions.keys())

    # Update routes
    await http_backend.update_routes(new_routes)

    # Verify new route was added
    assert len(http_backend.client_sessions) == 3
    assert new_route.route_id in http_backend.client_sessions
    assert len(http_backend.routes) == 3

    # Verify old sessions are still there
    for route_id in initial_session_ids:
        assert route_id in http_backend.client_sessions


@pytest.mark.asyncio
async def test_update_routes_remove_routes(http_backend, sample_routes):
    """Test removing routes from HTTPBackend."""
    # Remove one route
    new_routes = [sample_routes[0]]
    removed_route_id = sample_routes[1].route_id

    # Verify initial state
    assert len(http_backend.client_sessions) == 2
    assert removed_route_id in http_backend.client_sessions

    # Update routes
    await http_backend.update_routes(new_routes)

    # Verify route was removed
    assert len(http_backend.client_sessions) == 1
    assert removed_route_id not in http_backend.client_sessions
    assert len(http_backend.routes) == 1
    assert http_backend.routes[0].route_id == sample_routes[0].route_id


@pytest.mark.asyncio
async def test_update_routes_replace_all_routes(http_backend):
    """Test replacing all routes with completely new ones."""
    # Create completely new routes
    new_routes = [
        RouteInfo(
            route_id=uuid4(),
            session_id=uuid4(),
            session_name="new_session1",
            kernel_host="newhost",
            kernel_port=9001,
            protocol=ProxyProtocol.HTTP,
            traffic_ratio=1.0,
            last_health_check=0,
            consecutive_failures=0,
            health_status=ModelServiceStatus.HEALTHY,
        ),
        RouteInfo(
            route_id=uuid4(),
            session_id=uuid4(),
            session_name="new_session2",
            kernel_host="newhost",
            kernel_port=9002,
            protocol=ProxyProtocol.HTTP,
            traffic_ratio=1.0,
            last_health_check=0,
            consecutive_failures=0,
            health_status=ModelServiceStatus.HEALTHY,
        ),
    ]

    # Store old route IDs
    old_route_ids = set(http_backend.client_sessions.keys())

    # Update routes
    await http_backend.update_routes(new_routes)

    # Verify all old sessions were closed and new ones created
    assert len(http_backend.client_sessions) == 2
    new_route_ids = set(http_backend.client_sessions.keys())
    assert old_route_ids.isdisjoint(new_route_ids)
    assert len(http_backend.routes) == 2

    # Verify client sessions point to correct hosts
    for route in new_routes:
        session = http_backend.client_sessions[route.route_id]
        expected_base_url = f"http://{route.kernel_host}:{route.kernel_port}"
        assert str(session._base_url) == expected_base_url


@pytest.mark.asyncio
async def test_update_routes_empty_routes(http_backend):
    """Test updating with empty route list."""
    # Verify initial state
    assert len(http_backend.client_sessions) == 2

    # Update with empty routes
    await http_backend.update_routes([])

    # Verify all sessions were removed
    assert len(http_backend.client_sessions) == 0
    assert len(http_backend.routes) == 0


@pytest.mark.asyncio
async def test_update_routes_same_routes(http_backend, sample_routes):
    """Test updating with the same routes (no changes)."""
    # Store references to existing sessions
    original_sessions = dict(http_backend.client_sessions)

    # Update with same routes
    await http_backend.update_routes(sample_routes)

    # Verify no changes occurred
    assert len(http_backend.client_sessions) == 2
    assert len(http_backend.routes) == 2

    # Verify same client sessions are still used
    for route_id, session in original_sessions.items():
        assert http_backend.client_sessions[route_id] is session


@pytest.mark.asyncio
async def test_update_routes_mixed_changes(http_backend, sample_routes):
    """Test updating with mixed add/remove operations."""
    # Keep first route, remove second, add new one
    keep_route = sample_routes[0]
    new_route = RouteInfo(
        route_id=uuid4(),
        session_id=uuid4(),
        session_name="mixed_session",
        kernel_host="mixedhost",
        kernel_port=7001,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=1.0,
        last_health_check=0,
        consecutive_failures=0,
        health_status=ModelServiceStatus.HEALTHY,
    )
    mixed_routes = [keep_route, new_route]

    # Store original session for kept route
    kept_session = http_backend.client_sessions[keep_route.route_id]
    removed_route_id = sample_routes[1].route_id

    # Update routes
    await http_backend.update_routes(mixed_routes)

    # Verify changes
    assert len(http_backend.client_sessions) == 2
    assert keep_route.route_id in http_backend.client_sessions
    assert new_route.route_id in http_backend.client_sessions
    assert removed_route_id not in http_backend.client_sessions

    # Verify kept session is unchanged
    assert http_backend.client_sessions[keep_route.route_id] is kept_session

    # Verify new session has correct base URL
    new_session = http_backend.client_sessions[new_route.route_id]
    expected_base_url = f"http://{new_route.kernel_host}:{new_route.kernel_port}"
    assert str(new_session._base_url) == expected_base_url


@pytest.mark.asyncio
async def test_update_routes_concurrent_safety(http_backend, sample_routes):
    """Test that update_routes is thread-safe with route_lock."""

    # This test ensures the route_lock prevents race conditions
    async def concurrent_update(routes):
        await http_backend.update_routes(routes)

    # Create multiple different route configurations
    routes1 = [sample_routes[0]]
    routes2 = sample_routes
    routes3 = []

    # Run concurrent updates
    await asyncio.gather(
        concurrent_update(routes1),
        concurrent_update(routes2),
        concurrent_update(routes3),
    )

    # Final state should be consistent (empty routes from routes3)
    assert len(http_backend.client_sessions) == 0
    assert len(http_backend.routes) == 0
