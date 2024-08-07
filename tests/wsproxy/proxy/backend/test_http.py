import random
import unittest
import uuid
from unittest.mock import MagicMock

from ai.backend.wsproxy.exceptions import WorkerNotAvailable
from ai.backend.wsproxy.proxy.backend.http import HTTPBackend
from ai.backend.wsproxy.types import RouteInfo


class TestHTTPBackend(unittest.TestCase):
    def setUp(self):
        """Set up the HTTPBackend with predefined routes for testing."""
        self.backend = HTTPBackend(
            root_context=MagicMock(), circuit=MagicMock(), routes=self._create_routes()
        )

    def _create_routes(self):
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

    def test_no_routes(self):
        """Test that WorkerNotAvailable is raised when there are no routes."""
        self.backend.routes = []
        with self.assertRaises(WorkerNotAvailable):
            self.backend.selected_route

    def test_single_route_zero_traffic(self):
        """Test that WorkerNotAvailable is raised when the only route has zero traffic ratio."""
        self.backend.routes = [
            RouteInfo(
                session_id=uuid.uuid4(),
                session_name=None,
                kernel_host="localhost",
                kernel_port=8080,
                protocol="http",
                traffic_ratio=0,
            )
        ]
        with self.assertRaises(WorkerNotAvailable):
            self.backend.selected_route

    def test_multiple_routes(self):
        """
        Test that the correct route is selected based on the random value.

        This test covers different ranges:
        - 0-20% selects the last route with 20% traffic ratio
        - 20-50% selects the middle route with 30% traffic ratio
        - 50-100% selects the first route with 50% traffic ratio
        """
        test_cases = [
            {
                "random_value": 0.1,
                "expected_ratio": 0.2,
                "description": "Selects the last route with 20% traffic ratio (0-20% range)",
            },
            {
                "random_value": 0.25,
                "expected_ratio": 0.3,
                "description": "Selects the middle route with 30% traffic ratio (20-50% range)",
            },
            {
                "random_value": 0.6,
                "expected_ratio": 0.5,
                "description": "Selects the first route with 50% traffic ratio (50-100% range)",
            },
            {
                "random_value": 0.49,
                "expected_ratio": 0.3,
                "description": "Edge case that selects the middle route at the upper boundary of 20-50% range",
            },
            {
                "random_value": 0.99,
                "expected_ratio": 0.5,
                "description": "Edge case that selects the first route at the upper boundary of 50-100% range",
            },
        ]

        for case in test_cases:
            with self.subTest(case=case):
                random.random = MagicMock(return_value=case["random_value"])
                route = self.backend.selected_route
                self.assertEqual(
                    route.traffic_ratio, case["expected_ratio"], msg=case["description"]
                )
