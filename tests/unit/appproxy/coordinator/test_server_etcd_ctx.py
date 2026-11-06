from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.coordinator.config import TraefikConfig
from ai.backend.appproxy.coordinator.server import etcd_ctx
from ai.backend.common.configs.etcd import EtcdConfig


class TestEtcdCtx:
    @pytest.fixture
    def root_ctx_with_traefik_etcd_user_and_password(self) -> MagicMock:
        etcd_config = EtcdConfig.model_validate({
            "namespace": "traefik",
            "addr": {"host": "127.0.0.1", "port": 2379},
            "user": "backend",
            "password": "secret",
        })
        root_ctx = MagicMock()
        root_ctx.local_config.proxy_coordinator.enable_traefik = True
        root_ctx.local_config.proxy_coordinator.traefik = TraefikConfig(
            etcd=etcd_config, client_ip_strategy=None
        )
        return root_ctx

    async def test_creates_traefik_etcd_with_user_and_password(
        self, root_ctx_with_traefik_etcd_user_and_password: MagicMock
    ) -> None:
        async with etcd_ctx(root_ctx_with_traefik_etcd_user_and_password):
            assert isinstance(
                root_ctx_with_traefik_etcd_user_and_password.traefik_etcd, TraefikEtcd
            )
