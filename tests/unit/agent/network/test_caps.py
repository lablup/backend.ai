import json
from collections.abc import Mapping
from typing import Any, cast, override

from ai.backend.agent.network.caps import (
    compute_caps,
    parse_tunnel_offload,
    publish_backend,
    publish_caps,
    publish_vtep,
    withdraw_caps,
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

    async def compare_and_put(
        self,
        key: str,
        val: str,
        *,
        expected: str | None,
        guards: "Mapping[str, str | None]",
        **kwargs: Any,
    ) -> bool:
        """The store's own compare-and-swap, modelled because it is the fence being tested.

        The target must hold ``expected`` (absent when that is None) AND every guard must hold
        exactly what it is given (absent when that is None). All of it or none of it.
        """
        if self.puts.get(key) != expected:
            return False
        for guard_key, guard_val in guards.items():
            if self.puts.get(guard_key) != guard_val:
                return False
        self.puts[key] = val
        self.order.append(("put", key))
        return True

    async def compare_and_delete(
        self, key: str, expected: str, *, guards: "Mapping[str, str | None]", **kwargs: Any
    ) -> bool:
        if self.puts.get(key) != expected:
            return False
        for guard_key, guard_val in guards.items():
            if self.puts.get(guard_key) != guard_val:
                return False
        self.puts.pop(key, None)
        self.deleted.append(key)
        self.order.append(("delete", key))
        return True

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


class _NewRunLandsMidway(_CapturingEtcd):
    """A store where a NEWER run of the same agent id takes the id the moment this one looks.

    The window is between whatever this process last read and the write it makes off the back of
    it, so the injection goes on the first read: after that, every write this process makes is one
    it decided on stale information.
    """

    def __init__(self) -> None:
        super().__init__()
        self._landed = False

    @override
    async def get(self, key: str, **kwargs: Any) -> str | None:
        answer = await super().get(key)
        if not self._landed:
            self._landed = True
            self.puts["network/agent/i-abc123/boot"] = "run-2"
            self.puts["network/agent/i-abc123/caps"] = '{"from": "run-2"}'
            self.puts["network/agent/i-abc123/ready"] = "run-2-digest"
        return answer


class TestTwoRunsOfOneAgentId:
    """An agent id restarted quickly has two processes alive at once. Whichever of them writes
    last wins the key, and both outcomes are wrong: the old run's shutdown deleting the new run's
    advert leaves a node that is up and serving invisible to every placement, and the old run's
    last refresh landing on top leaves a fresh, correct-looking record describing a process that
    is going away."""

    async def test_an_older_run_does_not_publish_over_a_newer_one(self) -> None:
        etcd = _CapturingEtcd()
        etcd.puts["network/agent/i-abc123/boot"] = "run-2"
        caps = AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"])

        await publish_caps(
            cast(AbstractKVStore, etcd), "i-abc123", caps, vtep_ip="10.0.0.1", boot_id="run-1"
        )

        assert "network/agent/i-abc123/caps" not in etcd.puts
        assert "network/agent/i-abc123/ready" not in etcd.puts

    async def test_an_older_run_does_not_withdraw_a_newer_ones_advert(self) -> None:
        etcd = _CapturingEtcd()
        etcd.puts["network/agent/i-abc123/boot"] = "run-2"
        caps = AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"])
        await publish_caps(
            cast(AbstractKVStore, etcd), "i-abc123", caps, vtep_ip="10.0.0.1", boot_id="run-2"
        )

        await withdraw_caps(cast(AbstractKVStore, etcd), "i-abc123", boot_id="run-1")

        assert "network/agent/i-abc123/caps" in etcd.puts
        assert "network/agent/i-abc123/ready" in etcd.puts

    async def test_a_new_run_landing_mid_publish_is_not_overwritten(self) -> None:
        """The check and the write are two operations, and the new run publishes between them.
        Reading the boot key first only narrows that; the condition has to travel WITH the write.
        """
        caps = AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"])

        racing = _NewRunLandsMidway()
        racing.puts["network/agent/i-abc123/boot"] = "run-1"

        await publish_caps(
            cast(AbstractKVStore, racing), "i-abc123", caps, vtep_ip="10.0.0.1", boot_id="run-1"
        )

        assert racing.puts["network/agent/i-abc123/caps"] == '{"from": "run-2"}'
        assert racing.puts["network/agent/i-abc123/ready"] == "run-2-digest"

    async def test_a_new_run_landing_mid_withdraw_keeps_its_advert(self) -> None:
        racing = _NewRunLandsMidway()
        racing.puts["network/agent/i-abc123/boot"] = "run-1"
        racing.puts["network/agent/i-abc123/caps"] = '{"from": "run-2"}'
        racing.puts["network/agent/i-abc123/ready"] = "run-2-digest"

        await withdraw_caps(cast(AbstractKVStore, racing), "i-abc123", boot_id="run-1")

        assert racing.puts["network/agent/i-abc123/caps"] == '{"from": "run-2"}'
        assert racing.puts["network/agent/i-abc123/ready"] == "run-2-digest"

    async def test_the_current_run_publishes_and_withdraws_its_own(self) -> None:
        etcd = _CapturingEtcd()
        etcd.puts["network/agent/i-abc123/boot"] = "run-2"
        caps = AgentNetworkCaps(tunnel_offload=False, backends=["vxlan"])

        await publish_caps(
            cast(AbstractKVStore, etcd), "i-abc123", caps, vtep_ip="10.0.0.1", boot_id="run-2"
        )
        assert "network/agent/i-abc123/ready" in etcd.puts

        await withdraw_caps(cast(AbstractKVStore, etcd), "i-abc123", boot_id="run-2")

        assert "network/agent/i-abc123/caps" not in etcd.puts
        assert "network/agent/i-abc123/ready" not in etcd.puts


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
