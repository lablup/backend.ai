from __future__ import annotations

from typing import Any

import pytest


def _ingress_payload(frontend: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "id": "ingress-1",
        "authority": "worker-1",
        "revision": 1,
        "frontend": frontend,
        "access": {"mode": "public", "allowed_client_ips": []},
        "backend": {
            "id": "backend-1",
            "target_groups": [
                {
                    "id": "group-1",
                    "weight": 1,
                    "targets": [{"id": "target-1", "host": "10.0.0.1", "port": 8080}],
                }
            ],
        },
        **extra,
    }


@pytest.fixture
def port_ingress_payload() -> dict[str, Any]:
    return _ingress_payload({"kind": "port", "protocol": "http", "port": {"number": 10205}})


@pytest.fixture
def wildcard_ingress_payload() -> dict[str, Any]:
    return _ingress_payload({
        "kind": "wildcard",
        "protocol": "http",
        "wildcard": {"subdomain": "app-1"},
    })
