import uuid

import pytest

from ai.backend.wsproxy.exceptions import WorkerNotAvailable
from ai.backend.wsproxy.proxy.backend.http import HTTPBackend
from ai.backend.wsproxy.types import RouteInfo


@pytest.fixture
def http_backend():
    return HTTPBackend(root_context=None, circuit=None, routes=create_routes())


def create_routes():
    """Create a list of RouteInfo objects with different traffic ratios."""
    return [
        RouteInfo(
            session_id=uuid.uuid4(),
            session_name=None,
            kernel_host="localhost",
            kernel_port=30729,
            protocol="http",
            traffic_ratio=0.5,
        ),
        RouteInfo(
            session_id=uuid.uuid4(),
            session_name=None,
            kernel_host="localhost",
            kernel_port=30730,
            protocol="http",
            traffic_ratio=0.3,
        ),
        RouteInfo(
            session_id=uuid.uuid4(),
            session_name=None,
            kernel_host="localhost",
            kernel_port=30731,
            protocol="http",
            traffic_ratio=0.2,
        ),
    ]


def test_no_routes(http_backend):
    """Test that WorkerNotAvailable is raised when there are no routes."""
    http_backend.routes = []
    with pytest.raises(WorkerNotAvailable):
        _ = http_backend.selected_route


def test_single_route_zero_traffic(http_backend):
    """Test that WorkerNotAvailable is raised when the only route has zero traffic ratio."""
    http_backend.routes = [
        RouteInfo(
            session_id=uuid.uuid4(),
            session_name=None,
            kernel_host="localhost",
            kernel_port=8080,
            protocol="http",
            traffic_ratio=0,
        )
    ]
    with pytest.raises(WorkerNotAvailable):
        _ = http_backend.selected_route


@pytest.mark.parametrize(
    "random_value,expected_ratio,description",
    [
        (0.1, 0.2, "A random value of 0.1 selects a route with a 20% traffic ratio."),
        (0.4, 0.3, "A random value of 0.25 selects a route with a 30% traffic ratio."),
        (0.8, 0.5, "A random value of 0.6 selects a route with a 50% traffic ratio."),
        # Edge Case
        (0.0, 0.2, "A random value of 0.0 selects a route with a 20% traffic ratio."),
        (0.2, 0.3, "A random value of 0.2 selects a route with a 30% traffic ratio."),
        (0.5, 0.5, "A random value of 0.5 selects a route with a 50% traffic ratio."),
        (1.0, 0.5, "A random value of 1.0 selects a route with a 50% traffic ratio."),
    ],
)
def test_multiple_routes(http_backend, mocker, random_value, expected_ratio, description):
    """
    Test that the correct route is selected based on the random value.
    """
    mocker.patch("random.random", return_value=random_value)
    route = http_backend.selected_route
    assert route.traffic_ratio == expected_ratio, description
