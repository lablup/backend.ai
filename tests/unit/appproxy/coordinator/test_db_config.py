from __future__ import annotations

from typing import Any

import pytest

from ai.backend.appproxy.common.config import HostPortPair
from ai.backend.appproxy.coordinator.config import DBConfig
from ai.backend.common.exception import BackendAISchemaValidationFailed

_REQUIRED = {"type": "postgresql", "name": "appproxy", "user": "appproxy", "password": "pw"}


class TestDBConfigAddrs:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (
                {"addr": {"host": "db1", "port": 5432}},
                [HostPortPair(host="db1", port=5432)],
            ),
            (
                {"addrs": [{"host": "db1", "port": 5432}, {"host": "db2", "port": 5433}]},
                [HostPortPair(host="db1", port=5432), HostPortPair(host="db2", port=5433)],
            ),
        ],
    )
    def test_addrs(self, raw: dict[str, Any], expected: list[HostPortPair]) -> None:
        assert DBConfig.model_validate({**_REQUIRED, **raw}).addrs == expected

    def test_addrs_takes_precedence_over_addr(self) -> None:
        config = DBConfig.model_validate({
            **_REQUIRED,
            "addr": {"host": "db1", "port": 5432},
            "addrs": [{"host": "db2", "port": 5432}],
        })

        assert config.addrs == [HostPortPair(host="db2", port=5432)]

    @pytest.mark.parametrize("raw", [{}, {"addrs": []}])
    def test_missing_addrs_rejected(self, raw: dict[str, Any]) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            DBConfig.model_validate({**_REQUIRED, **raw})
