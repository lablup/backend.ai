from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.agent.containerd.intrinsic import CPUPlugin, MemoryPlugin


class TestDockerArgs:
    @pytest.mark.parametrize("plugin_cls", [CPUPlugin, MemoryPlugin])
    async def test_intrinsic_plugins_emit_no_docker_args(
        self, plugin_cls: type[CPUPlugin | MemoryPlugin]
    ) -> None:
        plugin = plugin_cls({}, {})

        assert await plugin.generate_docker_args(MagicMock(), {}) == {}
