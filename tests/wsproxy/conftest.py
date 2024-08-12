from datetime import datetime
from uuid import UUID

import pytest

from ai.backend.agent.utils import update_nested_dict
from ai.backend.wsproxy.types import AppMode, Circuit, FrontendMode, ProxyProtocol, RouteInfo


@pytest.fixture
def create_circuit():
    def _create_circuit(**overrides) -> Circuit:
        default_values = {
            "id": UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
            "app": "ttyd",
            "protocol": ProxyProtocol.HTTP,
            "worker": UUID("00000000-0000-0000-0000-000000000000"),
            "app_mode": AppMode.INTERACTIVE,
            "frontend_mode": FrontendMode.PORT,
            "envs": {},
            "arguments": None,
            "open_to_public": False,
            "allowed_client_ips": None,
            "port": 8080,
            "user_id": UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "endpoint_id": None,
            "route_info": [
                RouteInfo(
                    session_id=UUID("f5cd34ba-ae53-4537-a813-09f38496443d"),
                    session_name=None,
                    kernel_host="127.0.0.1",
                    kernel_port=30729,
                    protocol=ProxyProtocol.HTTP,
                    traffic_ratio=1.0,
                )
            ],
            "session_ids": [UUID("f5cd34ba-ae53-4537-a813-09f38496443d")],
            "created_at": datetime(2024, 7, 16, 5, 45, 45, 982446),
            "updated_at": datetime(2024, 7, 16, 5, 45, 45, 982452),
        }
        update_nested_dict(default_values, overrides)
        return Circuit(**default_values)

    return _create_circuit
