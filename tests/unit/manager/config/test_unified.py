import logging
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.unified import DatabaseConfig, ManagerConfig, MetricConfig

CONFIG_LOGGER = "ai.backend.common.config"


def test_config_validation_supports_field_name_and_alias() -> None:
    config = MetricConfig.model_validate({"address": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)

    config = MetricConfig.model_validate({"addr": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)


def _unknown_field_warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == CONFIG_LOGGER]


class TestUnknownFieldWarning:
    @pytest.mark.parametrize(
        "unknown_key",
        ["use-experimental-redis-event-dispatcher", "totally-made-up-key"],
    )
    def test_unknown_field_is_warned_and_kept(
        self,
        unknown_key: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level("WARNING", logger=CONFIG_LOGGER):
            config = ManagerConfig.model_validate({unknown_key: True}, by_name=True)

        warnings = _unknown_field_warnings(caplog)
        assert any(
            unknown_key in r.__dict__["log_tag_unknown_fields"]
            and r.__dict__["log_tag_config_type"] == "ManagerConfig"
            for r in warnings
        )
        assert config.model_dump()[unknown_key] is True
        assert unknown_key in config.model_fields_set

    def test_known_field_emits_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level("WARNING", logger=CONFIG_LOGGER):
            config = ManagerConfig.model_validate({"num-proc": 2}, by_name=True)

        assert _unknown_field_warnings(caplog) == []
        assert config.num_proc == 2


class TestDatabaseConfigAddrs:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (
                {"addr": {"host": "db.example.com", "port": 5432}},
                [HostPortPair(host="db.example.com", port=5432)],
            ),
            (
                {"addrs": ["db1:5432", "db2:5433"]},
                [HostPortPair(host="db1", port=5432), HostPortPair(host="db2", port=5433)],
            ),
            (
                {"addrs": [{"host": "[::1]", "port": 5432}]},
                [HostPortPair(host="::1", port=5432)],
            ),
            ({}, [HostPortPair(host="127.0.0.1", port=5432)]),
        ],
    )
    def test_addrs(self, raw: dict[str, Any], expected: list[HostPortPair]) -> None:
        assert DatabaseConfig.model_validate(raw).addrs == expected

    def test_addrs_takes_precedence_over_addr(self) -> None:
        config = DatabaseConfig.model_validate({"addr": "db1:5432", "addrs": ["db2:5432"]})

        assert config.addrs == [HostPortPair(host="db2", port=5432)]

    def test_addr_config_survives_dump_and_reload(self) -> None:
        config = DatabaseConfig.model_validate({"addr": "db1:5432"})

        reloaded = DatabaseConfig.model_validate(config.model_dump())

        assert reloaded.addrs == [HostPortPair(host="db1", port=5432)]

    def test_empty_addrs_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            DatabaseConfig.model_validate({"addrs": []})

    @pytest.mark.parametrize(
        ("addrs", "expected_host", "expected_port"),
        [
            (["db1:5432"], "db1", 5432),
            (["[::1]:5432"], "::1", 5432),
            (["db1:5432", "[fe80::1]:5433"], ["db1", "fe80::1"], [5432, 5433]),
        ],
    )
    def test_sqlalchemy_url_reaches_asyncpg_as_host_port_lists(
        self,
        addrs: list[str],
        expected_host: str | list[str],
        expected_port: int | list[int],
    ) -> None:
        config = DatabaseConfig.model_validate({"addrs": addrs, "password": "p@ss:/w"})

        url = config.sqlalchemy_url()
        engine = create_async_engine(url)

        _, connect_args = engine.dialect.create_connect_args(url)

        assert connect_args["host"] == expected_host
        assert connect_args["port"] == expected_port
        assert connect_args["password"] == "p@ss:/w"
        assert connect_args["target_session_attrs"] == "primary"
