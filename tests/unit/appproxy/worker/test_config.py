from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from ai.backend.appproxy.common.types import FrontendMode
from ai.backend.appproxy.worker.config import (
    ProxyWorkerConfig,
    TraefikConfig,
    TraefikPortProxyConfig,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.typed_validators import AutoDirectoryPath


@pytest.fixture
def traefik_config(tmp_path: Path) -> TraefikConfig:
    auto_dir_adapter = TypeAdapter(AutoDirectoryPath)
    return TraefikConfig(
        api_port=8080,
        frontend_mode=FrontendMode.PORT,
        wildcard_domain=None,
        port_proxy=TraefikPortProxyConfig(
            advertised_host="localhost",
            port_range=(30000, 31000),
        ),
        last_used_time_marker_directory=auto_dir_adapter.validate_python(tmp_path),
    )


class TestTraefikConfig:
    def test_last_used_time_marker_directory_auto_creates_parents(
        self,
        traefik_config: TraefikConfig,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "non_existent_path" / str(uuid4())
            assert not nested_path.exists()

            auto_dir_adapter = TypeAdapter(AutoDirectoryPath)
            marker_directory = auto_dir_adapter.validate_python(nested_path)

            config = traefik_config.model_copy(
                update={"last_used_time_marker_directory": marker_directory}
            )

            assert config.last_used_time_marker_directory.exists()
            assert config.last_used_time_marker_directory.is_dir()


@pytest.fixture
def minimal_proxy_worker_config() -> dict[str, object]:
    """The smallest payload that satisfies every required `ProxyWorkerConfig` field.

    `user` and `group` are supplied explicitly because their default factories stat
    `server.py` relative to the source tree, which is not resolvable under the test
    sandbox.
    """
    return {
        "coordinator_endpoint": "http://127.0.0.1:10200",
        "authority": "worker-1",
        "frontend_mode": "port",
        "protocol": "http",
        "accepted_traffics": ["inference", "interactive"],
        "port_proxy": {
            "bind_host": "0.0.0.0",
            "bind_port_range": [10205, 10300],
        },
        "user": 1000,
        "group": 1000,
    }


class TestBackendConnectionPoolLimit:
    def test_defaults_to_the_previously_implicit_ceiling(
        self,
        minimal_proxy_worker_config: dict[str, object],
    ) -> None:
        """Upgrading without touching the config must not change the effective limit."""
        config = ProxyWorkerConfig.model_validate(minimal_proxy_worker_config)

        assert config.backend_connection_pool_limit == 100

    def test_accepts_a_raised_limit(
        self,
        minimal_proxy_worker_config: dict[str, object],
    ) -> None:
        config = ProxyWorkerConfig.model_validate({
            **minimal_proxy_worker_config,
            "backend_connection_pool_limit": 500,
        })

        assert config.backend_connection_pool_limit == 500

    @pytest.mark.parametrize("limit", [0, -1])
    def test_rejects_non_positive_limits(
        self,
        minimal_proxy_worker_config: dict[str, object],
        limit: int,
    ) -> None:
        """aiohttp reads `limit=0` as *unlimited*, which is a descriptor footgun here.

        The pool is keyed per route, so an unbounded ceiling scales with the number of
        live routes and can exhaust the process descriptor limit — which fails every
        route at once rather than only the saturated one. Require an explicit bound.
        """
        with pytest.raises(BackendAISchemaValidationFailed):
            ProxyWorkerConfig.model_validate({
                **minimal_proxy_worker_config,
                "backend_connection_pool_limit": limit,
            })
