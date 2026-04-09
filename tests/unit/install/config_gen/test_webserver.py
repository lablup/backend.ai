"""Tests for shared Webserver config generation."""

from __future__ import annotations

import pytest
import tomlkit

from ai.backend.install.config_gen.webserver import (
    WebserverParams,
    apply_webserver_config,
)

WEBSERVER_SAMPLE = """\
[service]
ip = "0.0.0.0"
port = 8090
wsproxy.url = ""

[ui]
menu_blocklist = "pipeline"

[api]
domain = "default"
endpoint = "https://api.backend.ai"

[session]

[session.redis]
addr = "localhost:8111"

[session.redis.redis_helper_config]
"""


def _load_doc() -> tomlkit.TOMLDocument:
    return tomlkit.loads(WEBSERVER_SAMPLE)


class TestApplyWebserverConfig:
    @pytest.fixture()
    def params(self) -> WebserverParams:
        return WebserverParams(
            manager_host="127.0.0.1",
            manager_port=8091,
            redis_addr="127.0.0.1:8110",
        )

    def test_api_endpoint(self, params: WebserverParams) -> None:
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert doc["api"]["endpoint"] == "http://127.0.0.1:8091"

    def test_redis_single_mode(self, params: WebserverParams) -> None:
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert doc["session"]["redis"]["addr"] == "127.0.0.1:8110"
        assert "sentinel" not in doc["session"]["redis"]

    def test_redis_sentinel_mode(self) -> None:
        params = WebserverParams(
            redis_sentinel="10.0.0.1:26379,10.0.0.2:26379",
            redis_service_name="mymaster",
            redis_password="secret",
        )
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert doc["session"]["redis"]["sentinel"] == "10.0.0.1:26379,10.0.0.2:26379"
        assert doc["session"]["redis"]["service_name"] == "mymaster"
        assert doc["session"]["redis"]["password"] == "secret"
        assert "addr" not in doc["session"]["redis"]

    def test_redis_helper_config(self, params: WebserverParams) -> None:
        doc = _load_doc()
        apply_webserver_config(doc, params)
        helper = doc["session"]["redis"]["redis_helper_config"]
        assert helper["socket_timeout"] == 5.0
        assert helper["socket_connect_timeout"] == 2.0

    def test_wsproxy_url(self) -> None:
        params = WebserverParams(wsproxy_url="https://proxy.example.com:5050")
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert doc["service"]["wsproxy"]["url"] == "https://proxy.example.com:5050"

    def test_wsproxy_url_empty_not_set(self, params: WebserverParams) -> None:
        doc = _load_doc()
        apply_webserver_config(doc, params)
        # wsproxy.url is a dotted key in TOML, accessed as nested table
        assert doc["service"]["wsproxy"]["url"] == ""

    def test_force_endpoint_protocol(self) -> None:
        params = WebserverParams(force_endpoint_protocol="https")
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert doc["service"]["force_endpoint_protocol"] == "https"

    def test_no_force_endpoint_protocol(self, params: WebserverParams) -> None:
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert "force_endpoint_protocol" not in doc["service"]

    def test_ui_menus(self, params: WebserverParams) -> None:
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert doc["ui"]["menu_blocklist"] == "pipeline"
        assert doc["ui"]["menu_inactivelist"] == "statistics"

    def test_custom_menus(self) -> None:
        params = WebserverParams(
            menu_blocklist=["pipeline", "model-serving"],
            menu_inactivelist=[],
        )
        doc = _load_doc()
        apply_webserver_config(doc, params)
        assert doc["ui"]["menu_blocklist"] == "pipeline,model-serving"

    def test_toml_roundtrip(self, params: WebserverParams) -> None:
        doc = _load_doc()
        apply_webserver_config(doc, params)
        output = tomlkit.dumps(doc)
        reparsed = tomlkit.loads(output)
        assert reparsed["api"]["endpoint"] == "http://127.0.0.1:8091"
        assert reparsed["session"]["redis"]["addr"] == "127.0.0.1:8110"
