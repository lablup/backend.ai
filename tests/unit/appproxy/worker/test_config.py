from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

from ai.backend.appproxy.common.types import FrontendMode
from ai.backend.appproxy.worker.config import TraefikConfig, TraefikPortProxyConfig


class TestTraefikConfig:
    def test_last_used_time_marker_directory_auto_creates_parents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "non_existent_path" / str(uuid4())
            assert not nested_path.exists()

            config = TraefikConfig(
                api_port=8080,
                frontend_mode=FrontendMode.PORT,
                wildcard_domain=None,
                port_proxy=TraefikPortProxyConfig(
                    advertised_host="localhost",
                    port_range=(30000, 31000),
                ),
                last_used_time_marker_directory=str(nested_path),  # type: ignore[arg-type]
            )

            assert config.last_used_time_marker_directory.exists()
            assert config.last_used_time_marker_directory.is_dir()
