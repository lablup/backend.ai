import json
from typing import Any, cast

from ai.backend.agent.network.caps import (
    compute_caps,
    parse_tunnel_offload,
    publish_backend,
    publish_caps,
    publish_vtep,
)
from ai.backend.agent.network.readiness import Readiness
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.network.types import OVERLAY_ENCRYPTION_PROFILE, AgentNetworkCaps

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
    def test_advertises_vxlan(self) -> None:
        caps = compute_caps(tunnel_offload=True)
        assert caps.backends == ["vxlan"]
        assert caps.tunnel_offload is True

    def test_carries_the_tunnel_offload_flag(self) -> None:
        caps = compute_caps(tunnel_offload=False)
        assert caps.backends == ["vxlan"]
        assert caps.tunnel_offload is False


class TestPublishBackend:
    async def test_writes_backend_to_expected_key(self) -> None:
        etcd = _CapturingEtcd()
        await publish_backend(cast(AbstractKVStore, etcd), "i-abc123", "containerd")
        assert etcd.puts["network/agent/i-abc123/backend"] == "containerd"


class TestPublishVtep:
    async def test_writes_vtep_to_expected_key(self) -> None:
        etcd = _CapturingEtcd()
        await publish_vtep(cast(AbstractKVStore, etcd), "i-abc123", "192.168.105.7")
        assert etcd.puts["network/agent/i-abc123/vtep"] == "192.168.105.7"


class _CapturingEtcd:
    def __init__(self) -> None:
        self.puts: dict[str, str] = {}
        self.deleted: list[str] = []
        #: Every write in the order it happened. The order is the contract between the capability
        #: record and the readiness fence, so a test has to be able to see it.
        self.order: list[tuple[str, str]] = []

    async def delete(self, key: str, **kwargs: Any) -> None:
        self.puts.pop(key, None)
        self.deleted.append(key)
        self.order.append(("delete", key))

    async def get(self, key: str, **kwargs: Any) -> str | None:
        return self.puts.get(key)

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self.puts[key] = val
        self.order.append(("put", key))


class TestPublishCaps:
    async def test_writes_json_caps_to_expected_key(self) -> None:
        etcd = _CapturingEtcd()
        caps = AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"])
        await publish_caps(cast(AbstractKVStore, etcd), "i-abc123", caps)
        raw = etcd.puts["network/agent/i-abc123/caps"]
        payload = json.loads(raw)
        assert payload["backends"] == ["vxlan"]
        assert payload["tunnel_offload"] is False


class TestTheReadinessFenceIsNeverAheadOfTheRecord:
    """The record and the fence are two writes, and a manager reads between them. A create is
    admitted on the pair and its READY check is conditional on the fence, so the order decides
    whether a node whose endpoint has already moved can still have a session declared on it."""

    async def test_a_heartbeat_leaves_the_fence_alone(self) -> None:
        etcd = _CapturingEtcd()
        caps = AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"])
        await publish_caps(cast(AbstractKVStore, etcd), "i-abc123", caps, vtep_ip="10.0.0.1")
        first = etcd.puts["network/agent/i-abc123/ready"]
        etcd.deleted.clear()

        await publish_caps(cast(AbstractKVStore, etcd), "i-abc123", caps, vtep_ip="10.0.0.1")

        assert etcd.puts["network/agent/i-abc123/ready"] == first
        assert etcd.deleted == [], "an unchanged fence was taken down and put back"

    async def test_a_readiness_change_takes_the_old_fence_down_first(self) -> None:
        etcd = _CapturingEtcd()
        caps = AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"])
        await publish_caps(cast(AbstractKVStore, etcd), "i-abc123", caps, vtep_ip="10.0.0.1")
        before = etcd.puts["network/agent/i-abc123/ready"]
        etcd.order.clear()

        await publish_caps(cast(AbstractKVStore, etcd), "i-abc123", caps, vtep_ip="10.0.0.2")

        assert etcd.puts["network/agent/i-abc123/ready"] != before
        # Down, then the record, then up: the worst a reader sees is "not admitting", which is
        # true. The other order leaves the old fence standing over a record it no longer matches.
        assert etcd.order == [
            ("delete", "network/agent/i-abc123/ready"),
            ("put", "network/agent/i-abc123/caps"),
            ("put", "network/agent/i-abc123/ready"),
        ]

    async def test_a_diagnostic_that_flapped_does_not_move_the_fence(self) -> None:
        # `tunnel_offload` comes from running ethtool, which fails transiently and answers False
        # when it does. The overlay works either way, so it must not break a live create.
        etcd = _CapturingEtcd()
        await publish_caps(
            cast(AbstractKVStore, etcd),
            "i-abc123",
            AgentNetworkCaps(tunnel_offload=True, backends=["vxlan"]),
            vtep_ip="10.0.0.1",
        )
        before = etcd.puts["network/agent/i-abc123/ready"]

        await publish_caps(
            cast(AbstractKVStore, etcd),
            "i-abc123",
            AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"]),
            vtep_ip="10.0.0.1",
        )

        assert etcd.puts["network/agent/i-abc123/ready"] == before


class TestTheOverlayEncryptionProfile:
    """The manager will not encrypt a session unless every node it lands on names this exact
    string. It says the node can hold up its end of an ESP tunnel built the way this version
    builds it -- transport mode, AES-GCM, ESN, per-pair-and-generation keys."""

    def test_a_node_that_can_serve_the_overlay_publishes_it(self) -> None:
        caps = compute_caps(tunnel_offload=False, readiness=Readiness())
        assert caps.encryption_profiles == [OVERLAY_ENCRYPTION_PROFILE]

    def test_a_node_that_cannot_serve_it_publishes_none(self) -> None:
        # No `u32`, no `policy` match: it cannot hold up an ENCRYPTED tunnel either, and saying so
        # is what keeps the manager from placing an encrypted session here.
        caps = compute_caps(
            tunnel_offload=False,
            readiness=Readiness(blocking=("iptables has no `u32` match",)),
        )
        assert caps.encryption_profiles == []
        assert caps.backends == []

    def test_an_absent_field_defaults_to_none(self) -> None:
        # What an agent from before this contract published; the manager reads it as "cannot".
        assert AgentNetworkCaps(tunnel_offload=False).encryption_profiles == []
