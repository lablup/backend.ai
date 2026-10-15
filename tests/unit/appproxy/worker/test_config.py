from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from ai.backend.appproxy.common.types import FrontendMode
from ai.backend.appproxy.worker.config import (
    IngressConfig,
    IngressLayerType,
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


class TestIngressConfig:
    def test_default_is_in_memory_only(self) -> None:
        config = IngressConfig.model_validate({})
        assert config.layers == [IngressLayerType.IN_MEMORY]
        assert config.redis.key_prefix == "appproxy:ingress"

    @pytest.mark.parametrize(
        "layers",
        [["in-memory"], ["in-memory", "redis"], ["redis"], ["redis", "in-memory"]],
    )
    def test_supported_layers_are_accepted(self, layers: list[str]) -> None:
        config = IngressConfig.model_validate({"layers": layers})
        assert config.layers == layers

    def test_empty_layers_are_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressConfig.model_validate({"layers": []})

    def test_repeated_layer_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressConfig.model_validate({"layers": ["in-memory", "in-memory"]})

    def test_unknown_layer_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressConfig.model_validate({"layers": ["memory"]})

    def test_redis_key_prefix_is_read_from_kebab_case(self) -> None:
        config = IngressConfig.model_validate({"redis": {"key-prefix": "custom:ingress"}})
        assert config.redis.key_prefix == "custom:ingress"

    def test_in_memory_ttl_is_unset_by_default(self) -> None:
        config = IngressConfig.model_validate({})
        assert config.in_memory.ttl is None
        assert config.in_memory.negative_ttl is None

    def test_in_memory_ttl_with_redis_is_accepted(self) -> None:
        config = IngressConfig.model_validate({
            "layers": ["in-memory", "redis"],
            "in-memory": {"ttl": 60.0, "negative-ttl": 5.0},
        })
        assert config.in_memory.ttl == 60.0
        assert config.in_memory.negative_ttl == 5.0

    @pytest.mark.parametrize("ttl_key", ["ttl", "negative-ttl"])
    @pytest.mark.parametrize("layers", [["in-memory"], ["redis", "in-memory"]])
    def test_in_memory_ttl_without_later_layer_is_rejected(
        self, ttl_key: str, layers: list[str]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressConfig.model_validate({"layers": layers, "in-memory": {ttl_key: 60.0}})

    def test_non_positive_ttl_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            IngressConfig.model_validate({
                "layers": ["in-memory", "redis"],
                "in-memory": {"ttl": 0},
            })
