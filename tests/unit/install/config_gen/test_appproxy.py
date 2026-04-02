"""Tests for shared AppProxy config generation."""

from __future__ import annotations

import pytest
import tomlkit

from ai.backend.install.config_gen.appproxy import (
    CoordinatorParams,
    WorkerParams,
    apply_coordinator_config,
    apply_worker_config,
)
from ai.backend.install.types import FrontendMode

COORDINATOR_SAMPLE = """\
[db]
type = "postgresql"
name = "appproxy"
user = "appproxy"
password = "placeholder"
pool_size = 8
max_overflow = 64
[db.addr]
host = "127.0.0.1"
port = 8100

[redis]
addr = { host = "127.0.0.1", port = 8110 }

[proxy_coordinator]
tls_listen = false
tls_advertised = false
[proxy_coordinator.bind_addr]
host = "0.0.0.0"
port = 10200
[proxy_coordinator.advertised_addr]
# Change to actual host
host = "127.0.0.1"
port = 10200

[secrets]
api_secret = "placeholder"
jwt_secret = "placeholder"

[permit_hash]
secret = "placeholder"
"""

WORKER_SAMPLE = """\
[redis]
addr = { host = "127.0.0.1", port = 8110 }

[proxy_worker]
coordinator_endpoint = "http://127.0.0.1:10200"
tls_listen = false
tls_advertised = false
frontend_mode = "port"
api_bind_addr = { host = "0.0.0.0", port = 10201 }
api_advertised_addr = { host = "127.0.0.1", port = 10201 }

[proxy_worker.port_proxy]
bind_host = "0.0.0.0"
advertised_host = "127.0.0.1"
bind_port_range = [10205, 10300]

[secrets]
api_secret = "placeholder"
jwt_secret = "placeholder"

[permit_hash]
secret = "placeholder"
"""


def _load_coordinator_doc() -> tomlkit.TOMLDocument:
    return tomlkit.loads(COORDINATOR_SAMPLE)


def _load_worker_doc() -> tomlkit.TOMLDocument:
    return tomlkit.loads(WORKER_SAMPLE)


class TestApplyCoordinatorConfig:
    @pytest.fixture()
    def params(self) -> CoordinatorParams:
        return CoordinatorParams(
            db_host="db.example.com",
            db_port=5432,
            api_secret="test-api-secret",
            jwt_secret="test-jwt-secret",
            permit_hash_secret="test-permit-hash",
        )

    def test_db_config_applied(self, params: CoordinatorParams) -> None:
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        assert doc["db"]["addr"]["host"] == "db.example.com"
        assert doc["db"]["addr"]["port"] == 5432
        assert doc["db"]["user"] == "appproxy"

    def test_redis_config_applied(self, params: CoordinatorParams) -> None:
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        assert doc["redis"]["addr"]["host"] == "127.0.0.1"
        assert doc["redis"]["addr"]["port"] == 8110

    def test_secrets_applied(self, params: CoordinatorParams) -> None:
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        assert doc["secrets"]["api_secret"] == "test-api-secret"
        assert doc["secrets"]["jwt_secret"] == "test-jwt-secret"
        assert doc["permit_hash"]["secret"] == "test-permit-hash"

    def test_bind_and_advertised_addr(self, params: CoordinatorParams) -> None:
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        assert doc["proxy_coordinator"]["bind_addr"]["host"] == "0.0.0.0"
        assert doc["proxy_coordinator"]["bind_addr"]["port"] == 10200

    def test_tls_advertised(self) -> None:
        params = CoordinatorParams(
            db_host="localhost",
            db_port=8100,
            tls_advertised=True,
            advertised_port=443,
        )
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        assert doc["proxy_coordinator"]["tls_advertised"] is True
        assert doc["proxy_coordinator"]["advertised_addr"]["port"] == 443

    def test_traefik_disabled_by_default(self, params: CoordinatorParams) -> None:
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        assert "traefik" not in doc["proxy_coordinator"]

    def test_traefik_enabled(self) -> None:
        params = CoordinatorParams(
            db_host="localhost",
            db_port=8100,
            enable_traefik=True,
            etcd_host="10.0.0.1",
            etcd_port=2379,
        )
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        assert doc["proxy_coordinator"]["enable_traefik"] is True
        assert doc["proxy_coordinator"]["traefik"]["etcd"]["addr"]["host"] == "10.0.0.1"

    def test_comments_preserved(self, params: CoordinatorParams) -> None:
        doc = _load_coordinator_doc()
        apply_coordinator_config(doc, params)
        output = tomlkit.dumps(doc)
        assert "# Change to actual host" in output


class TestApplyWorkerConfig:
    @pytest.fixture()
    def port_params(self) -> WorkerParams:
        return WorkerParams(
            api_secret="test-secret",
            jwt_secret="test-jwt",
            permit_hash_secret="test-hash",
            frontend_mode=FrontendMode.PORT,
            port_proxy_advertised_host="192.168.1.1",
        )

    def test_port_mode_applied(self, port_params: WorkerParams) -> None:
        doc = _load_worker_doc()
        apply_worker_config(doc, port_params)
        assert doc["proxy_worker"]["frontend_mode"] == "port"
        assert doc["proxy_worker"]["port_proxy"]["advertised_host"] == "192.168.1.1"

    def test_coordinator_endpoint(self, port_params: WorkerParams) -> None:
        doc = _load_worker_doc()
        apply_worker_config(doc, port_params)
        assert doc["proxy_worker"]["coordinator_endpoint"] == "http://127.0.0.1:10200"

    def test_secrets_applied(self, port_params: WorkerParams) -> None:
        doc = _load_worker_doc()
        apply_worker_config(doc, port_params)
        assert doc["secrets"]["api_secret"] == "test-secret"
        assert doc["permit_hash"]["secret"] == "test-hash"

    def test_wildcard_mode(self) -> None:
        params = WorkerParams(
            api_secret="s",
            jwt_secret="j",
            permit_hash_secret="p",
            frontend_mode=FrontendMode.WILDCARD,
            wildcard_domain=".proxy.example.com",
            wildcard_advertised_port=443,
        )
        doc = _load_worker_doc()
        apply_worker_config(doc, params)
        assert doc["proxy_worker"]["frontend_mode"] == "wildcard"
        assert "port_proxy" not in doc["proxy_worker"]
        assert doc["proxy_worker"]["wildcard_domain"]["domain"] == ".proxy.example.com"

    def test_wildcard_mode_without_domain(self) -> None:
        params = WorkerParams(
            api_secret="s",
            jwt_secret="j",
            permit_hash_secret="p",
            frontend_mode=FrontendMode.WILDCARD,
            wildcard_domain=None,
        )
        doc = _load_worker_doc()
        apply_worker_config(doc, params)
        assert "wildcard_domain" not in doc["proxy_worker"]

    def test_traefik_mode(self) -> None:
        params = WorkerParams(
            api_secret="s",
            jwt_secret="j",
            permit_hash_secret="p",
            frontend_mode=FrontendMode.TRAEFIK,
            traefik_etcd_host="10.0.0.1",
            traefik_etcd_port=2379,
            port_proxy_advertised_host="proxy.example.com",
        )
        doc = _load_worker_doc()
        apply_worker_config(doc, params)
        assert doc["proxy_worker"]["frontend_mode"] == "traefik"
        assert "port_proxy" not in doc["proxy_worker"]
        assert doc["proxy_worker"]["traefik"]["api_port"] == 18080
        assert doc["proxy_worker"]["traefik"]["etcd"]["addr"]["host"] == "10.0.0.1"
        assert (
            doc["proxy_worker"]["traefik"]["port_proxy"]["advertised_host"] == "proxy.example.com"
        )

    def test_tls_advertised(self) -> None:
        params = WorkerParams(
            api_secret="s",
            jwt_secret="j",
            permit_hash_secret="p",
            tls_advertised=True,
        )
        doc = _load_worker_doc()
        apply_worker_config(doc, params)
        assert doc["proxy_worker"]["tls_advertised"] is True

    def test_toml_roundtrip(self, port_params: WorkerParams) -> None:
        doc = _load_worker_doc()
        apply_worker_config(doc, port_params)
        output = tomlkit.dumps(doc)
        reparsed = tomlkit.loads(output)
        assert reparsed["proxy_worker"]["frontend_mode"] == "port"
        assert reparsed["secrets"]["api_secret"] == "test-secret"
