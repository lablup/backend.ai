from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.plugin.keypair.hook import KeypairAuthHookPlugin


class TestKeypairHookStartup:
    async def test_missing_secret_fails_plugin_loading(self) -> None:
        etcd = MagicMock(spec=AsyncEtcd)
        etcd.get_prefix = AsyncMock(return_value={})
        ctx = HookPluginContext(etcd, {})

        with (
            patch.object(
                HookPluginContext,
                "discover_plugins",
                return_value=[("auth_keypair", KeypairAuthHookPlugin)],
            ),
            pytest.raises(BackendAISchemaValidationFailed),
        ):
            await ctx.init(context={"webapp": {"openid": {}}}, allowlist={"auth_keypair"})
