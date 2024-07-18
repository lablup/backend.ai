import unittest
from unittest.mock import MagicMock
from ai.backend.wsproxy.proxy.backend.http import HTTPBackend
from ai.backend.wsproxy.types import RouteInfo
import uuid
from ai.backend.wsproxy.exceptions import WorkerNotAvailable
import random


class TestHTTPBackend(unittest.TestCase):

    def setUp(self):
        self.backend = HTTPBackend(
            root_context=MagicMock(),
            circuit=MagicMock(),
            routes=self._create_routes()
        )

    def _create_routes(self):
        return [
            RouteInfo(
                session_id=uuid.uuid4(),
                session_name=None,
                kernel_host='localhost',
                kernel_port=8080,
                protocol="http",
                traffic_ratio=0.5
            ),
            RouteInfo(
                session_id=uuid.uuid4(),
                session_name=None,
                kernel_host='localhost',
                kernel_port=8081,
                protocol="http",
                traffic_ratio=0.3
            ),
            RouteInfo(
                session_id=uuid.uuid4(),
                session_name=None,
                kernel_host='localhost',
                kernel_port=8082,
                protocol="http",
                traffic_ratio=0.2
            )
        ]

    def test_no_routes(self):
        self.backend.routes = []
        with self.assertRaises(WorkerNotAvailable):
            self.backend.selected_route

    def test_single_route_zero_traffic(self):
        self.backend.routes = [
            RouteInfo(
                session_id=uuid.uuid4(),
                session_name=None,
                kernel_host='localhost',
                kernel_port=8082,
                protocol="http",
                traffic_ratio=0
            )
        ]
        with self.assertRaises(WorkerNotAvailable):
            self.backend.selected_route

    def test_multiple_routes(self):
        test_cases = [
            (0.1, 0.2),
            (0.4, 0.3),
            (0.9, 0.5)
        ]

        for random_value, expected_ratio in test_cases:
            random.random = MagicMock(return_value=random_value)
            route = self.backend.selected_route
            self.assertEqual(route.traffic_ratio, expected_ratio)
