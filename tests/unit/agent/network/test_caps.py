import json
from typing import Any, cast

from ai.backend.agent.network.caps import (
    caps_key,
    compute_caps,
    parse_tunnel_offload,
    publish_caps,
)
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.network.types import AgentNetworkCaps

_ETHTOOL_OFF_FIXED = """\
Features for enp4s0:
rx-checksumming: on
tx-udp_tnl-segmentation: off [fixed]
tx-udp_tnl-csum-segmentation: off [fixed]
"""

_ETHTOOL_ON = """\
Features for eth0:
tx-udp_tnl-segmentation: on
tx-udp_tnl-csum-segmentation: on
"""

_ETHTOOL_ON_FIXED = """\
Features for eth0:
tx-udp_tnl-segmentation: on [fixed]
"""

_ETHTOOL_MISSING = """\
Features for eth0:
rx-checksumming: on
"""


class TestParseTunnelOffload:
    def test_off_fixed_is_false(self) -> None:
        assert parse_tunnel_offload(_ETHTOOL_OFF_FIXED) is False

    def test_on_is_true(self) -> None:
        assert parse_tunnel_offload(_ETHTOOL_ON) is True

    def test_on_fixed_is_true(self) -> None:
        assert parse_tunnel_offload(_ETHTOOL_ON_FIXED) is True

    def test_missing_feature_is_false(self) -> None:
        assert parse_tunnel_offload(_ETHTOOL_MISSING) is False

    def test_empty_output_is_false(self) -> None:
        assert parse_tunnel_offload("") is False


class TestComputeCaps:
    def test_native_routing_offers_host_gw(self) -> None:
        caps = compute_caps(tunnel_offload=True, native_routing_ok=True)
        assert caps.backends == ["vxlan", "host-gw"]
        assert caps.native_routing_ok is True

    def test_no_native_routing_only_vxlan(self) -> None:
        caps = compute_caps(tunnel_offload=False, native_routing_ok=False)
        assert caps.backends == ["vxlan"]
        assert caps.tunnel_offload is False


class TestCapsKey:
    def test_key_format(self) -> None:
        assert caps_key("i-abc123") == "network/agent/i-abc123/caps"


class _CapturingEtcd:
    def __init__(self) -> None:
        self.puts: dict[str, str] = {}

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self.puts[key] = val


class TestPublishCaps:
    async def test_writes_json_caps_to_expected_key(self) -> None:
        etcd = _CapturingEtcd()
        caps = AgentNetworkCaps(
            tunnel_offload=False, native_routing_ok=True, backends=["vxlan", "host-gw"]
        )
        await publish_caps(cast(AbstractKVStore, etcd), "i-abc123", caps)
        raw = etcd.puts["network/agent/i-abc123/caps"]
        payload = json.loads(raw)
        assert payload["native_routing_ok"] is True
        assert payload["backends"] == ["vxlan", "host-gw"]
        assert payload["tunnel_offload"] is False
