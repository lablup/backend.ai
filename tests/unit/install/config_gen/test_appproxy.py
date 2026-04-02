"""Tests for shared AppProxy config generation."""

from __future__ import annotations

import pytest

from ai.backend.install.config_gen.appproxy import (
    CoordinatorParams,
    WorkerParams,
    build_coordinator_config,
    build_worker_config,
)
from ai.backend.install.types import FrontendMode


class TestBuildCoordinatorConfig:
    @pytest.fixture()
    def params(self) -> CoordinatorParams:
        return CoordinatorParams(
            db_host="localhost",
            db_port=8100,
            api_secret="test-api-secret",
            jwt_secret="test-jwt-secret",
            permit_hash_secret="test-permit-hash",
        )

    def test_basic_structure(self, params: CoordinatorParams) -> None:
        config = build_coordinator_config(params)
        assert "db" in config
        assert "redis" in config
        assert "proxy_coordinator" in config
        assert "secrets" in config
        assert "permit_hash" in config

    def test_db_config(self, params: CoordinatorParams) -> None:
        config = build_coordinator_config(params)
        assert config["db"]["type"] == "postgresql"
        assert config["db"]["addr"]["host"] == "localhost"
        assert config["db"]["addr"]["port"] == 8100
        assert config["db"]["user"] == "appproxy"
        assert config["db"]["password"] == "develove"

    def test_redis_config(self, params: CoordinatorParams) -> None:
        config = build_coordinator_config(params)
        assert config["redis"]["addr"]["host"] == "127.0.0.1"
        assert config["redis"]["addr"]["port"] == 8110

    def test_secrets(self, params: CoordinatorParams) -> None:
        config = build_coordinator_config(params)
        assert config["secrets"]["api_secret"] == "test-api-secret"
        assert config["secrets"]["jwt_secret"] == "test-jwt-secret"
        assert config["permit_hash"]["secret"] == "test-permit-hash"

    def test_bind_and_advertised_addr(self, params: CoordinatorParams) -> None:
        config = build_coordinator_config(params)
        assert config["proxy_coordinator"]["bind_addr"]["host"] == "0.0.0.0"
        assert config["proxy_coordinator"]["bind_addr"]["port"] == 10200
        assert config["proxy_coordinator"]["advertised_addr"]["host"] == "127.0.0.1"

    def test_tls_advertised(self) -> None:
        params = CoordinatorParams(
            db_host="localhost",
            db_port=8100,
            tls_advertised=True,
            advertised_port=443,
        )
        config = build_coordinator_config(params)
        assert config["proxy_coordinator"]["tls_advertised"] is True
        assert config["proxy_coordinator"]["advertised_addr"]["port"] == 443

    def test_traefik_disabled_by_default(self, params: CoordinatorParams) -> None:
        config = build_coordinator_config(params)
        assert "traefik" not in config["proxy_coordinator"]
        assert config["proxy_coordinator"].get("enable_traefik") is None

    def test_traefik_enabled(self) -> None:
        params = CoordinatorParams(
            db_host="localhost",
            db_port=8100,
            enable_traefik=True,
            etcd_host="10.0.0.1",
            etcd_port=2379,
        )
        config = build_coordinator_config(params)
        assert config["proxy_coordinator"]["enable_traefik"] is True
        assert config["proxy_coordinator"]["traefik"]["etcd"]["addr"]["host"] == "10.0.0.1"
        assert config["proxy_coordinator"]["traefik"]["etcd"]["addr"]["port"] == 2379


class TestBuildWorkerConfig:
    @pytest.fixture()
    def port_params(self) -> WorkerParams:
        return WorkerParams(
            api_secret="test-secret",
            jwt_secret="test-jwt",
            permit_hash_secret="test-hash",
            frontend_mode=FrontendMode.PORT,
            port_proxy_advertised_host="192.168.1.1",
        )

    def test_port_mode_structure(self, port_params: WorkerParams) -> None:
        config = build_worker_config(port_params)
        assert config["proxy_worker"]["frontend_mode"] == "port"
        assert "port_proxy" in config["proxy_worker"]
        assert "wildcard_domain" not in config["proxy_worker"]
        assert "traefik" not in config["proxy_worker"]

    def test_port_mode_proxy_config(self, port_params: WorkerParams) -> None:
        config = build_worker_config(port_params)
        pp = config["proxy_worker"]["port_proxy"]
        assert pp["advertised_host"] == "192.168.1.1"
        assert pp["bind_port_range"] == [10205, 10300]

    def test_wildcard_mode(self) -> None:
        params = WorkerParams(
            api_secret="s",
            jwt_secret="j",
            permit_hash_secret="p",
            frontend_mode=FrontendMode.WILDCARD,
            wildcard_domain=".proxy.example.com",
            wildcard_advertised_port=443,
        )
        config = build_worker_config(params)
        assert config["proxy_worker"]["frontend_mode"] == "wildcard"
        assert "port_proxy" not in config["proxy_worker"]
        wd = config["proxy_worker"]["wildcard_domain"]
        assert wd["domain"] == ".proxy.example.com"
        assert wd["advertised_port"] == 443

    def test_wildcard_mode_without_domain(self) -> None:
        params = WorkerParams(
            api_secret="s",
            jwt_secret="j",
            permit_hash_secret="p",
            frontend_mode=FrontendMode.WILDCARD,
            wildcard_domain=None,
        )
        config = build_worker_config(params)
        assert "wildcard_domain" not in config["proxy_worker"]

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
        config = build_worker_config(params)
        assert config["proxy_worker"]["frontend_mode"] == "traefik"
        assert "port_proxy" not in config["proxy_worker"]
        traefik = config["proxy_worker"]["traefik"]
        assert traefik["api_port"] == 18080
        assert traefik["etcd"]["addr"]["host"] == "10.0.0.1"
        assert traefik["port_proxy"]["advertised_host"] == "proxy.example.com"

    def test_coordinator_endpoint(self, port_params: WorkerParams) -> None:
        config = build_worker_config(port_params)
        assert config["proxy_worker"]["coordinator_endpoint"] == "http://127.0.0.1:10200"

    def test_secrets_match_coordinator(self, port_params: WorkerParams) -> None:
        config = build_worker_config(port_params)
        assert config["secrets"]["api_secret"] == "test-secret"
        assert config["secrets"]["jwt_secret"] == "test-jwt"
        assert config["permit_hash"]["secret"] == "test-hash"

    def test_tls_advertised(self) -> None:
        params = WorkerParams(
            api_secret="s",
            jwt_secret="j",
            permit_hash_secret="p",
            tls_advertised=True,
        )
        config = build_worker_config(params)
        assert config["proxy_worker"]["tls_advertised"] is True
