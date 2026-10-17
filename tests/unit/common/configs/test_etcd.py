from typing import Any

import pytest

from ai.backend.common import config
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.typed_validators import HostPortPair

_ETCD_MEMBERS = ["etcd1:2379", "etcd2:2379", "etcd3:2379"]


class TestEtcdConfigAddrs:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (
                {"addrs": _ETCD_MEMBERS},
                [
                    HostPortPair(host="etcd1", port=2379),
                    HostPortPair(host="etcd2", port=2379),
                    HostPortPair(host="etcd3", port=2379),
                ],
            ),
            ({"addr": "etcd1:2379"}, [HostPortPair(host="etcd1", port=2379)]),
            (
                {"addr": ["etcd1:2379", "etcd2:2379"]},
                [HostPortPair(host="etcd1", port=2379), HostPortPair(host="etcd2", port=2379)],
            ),
            (
                {"addr": "etcd1:2379", "addrs": ["etcd2:2379"]},
                [HostPortPair(host="etcd2", port=2379)],
            ),
            ({}, [HostPortPair(host="127.0.0.1", port=2379)]),
        ],
    )
    def test_to_dataclass_addrs(self, raw: dict[str, Any], expected: list[HostPortPair]) -> None:
        assert EtcdConfig.model_validate(raw).to_dataclass().addrs == expected

    def test_addr_config_survives_dump_and_reload(self) -> None:
        etcd_config = EtcdConfig.model_validate({"addr": "etcd1:2379"})

        reloaded = EtcdConfig.model_validate(etcd_config.model_dump())

        assert reloaded.addrs == [HostPortPair(host="etcd1", port=2379)]

    def test_empty_addrs_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            EtcdConfig.model_validate({"addrs": []})


class TestEtcdConfigIvAddrs:
    @pytest.mark.parametrize(
        ("etcd", "expected"),
        [
            (
                {"addrs": _ETCD_MEMBERS},
                [("etcd1", 2379), ("etcd2", 2379), ("etcd3", 2379)],
            ),
            ({"addr": "etcd1:2379"}, [("etcd1", 2379)]),
            ({"addr": ["etcd1:2379", "etcd2:2379"]}, [("etcd1", 2379), ("etcd2", 2379)]),
            ({"addr": "etcd1:2379", "addrs": ["etcd2:2379"]}, [("etcd2", 2379)]),
            ({}, [("127.0.0.1", 2379)]),
        ],
    )
    def test_addrs(self, etcd: dict[str, Any], expected: list[tuple[str, int]]) -> None:
        checked = config.etcd_config_iv.check({"etcd": {"namespace": "local", **etcd}})

        assert [(str(addr.host), addr.port) for addr in checked["etcd"]["addrs"]] == expected
