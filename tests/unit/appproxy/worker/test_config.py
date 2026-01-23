from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from ai.backend.appproxy.common.types import FrontendMode
from ai.backend.appproxy.worker.config import TraefikConfig, TraefikPortProxyConfig
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
