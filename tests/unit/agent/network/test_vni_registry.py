"""Node-wide ownership of a VNI.

The privnet does not trust the agent with privileged networking, but it did take the network
configuration at face value: any VNI the agent named became the VNI whose `baivx*`, `baibr*` and
LOCAL bridge devices setup deletes and rebuilds. These pin the binding that stops one agent's
declaration from reaching into another session's data plane.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.network.vni_registry import (
    VniConflict,
    VniHolder,
    VniRegistry,
    config_digest,
)

_CONFIG = {
    "backend": "vxlan",
    "subnet": "10.128.5.0/24",
    "vni": 4138,
    "mtu": 1412,
    "vxlan_port": 4789,
    "encryption_key": "ab" * 32,
}


async def _bind(registry: VniRegistry, agent: str, session: str, config: dict[str, Any]) -> bool:
    async with registry.binding(int(config["vni"]), agent, session, config_digest(config)) as b:
        return b.recorded


async def _release(
    registry: VniRegistry, agent: str, session: str, config: dict[str, Any]
) -> bool | None:
    async with registry.releasing(
        int(config["vni"]), agent, session, config_digest(config)
    ) as freed:
        return freed


class TestTheDigest:
    def test_the_same_declaration_gives_the_same_digest(self) -> None:
        assert config_digest(dict(_CONFIG)) == config_digest(dict(_CONFIG))

    def test_a_changed_subnet_changes_it(self) -> None:
        assert config_digest({**_CONFIG, "subnet": "10.128.6.0/24"}) != config_digest(_CONFIG)

    def test_a_changed_key_changes_it(self) -> None:
        assert config_digest({**_CONFIG, "encryption_key": "cd" * 32}) != config_digest(_CONFIG)

    def test_a_field_the_devices_are_not_built_from_does_not(self) -> None:
        # Re-declaring with an extra field the data plane never sees is not a conflict.
        assert config_digest({**_CONFIG, "comment": "hello"}) == config_digest(_CONFIG)


class TestBinding:
    def _registry(self, tmp_path: Path) -> VniRegistry:
        return VniRegistry(tmp_path / "vni")

    async def test_a_free_vni_is_bound(self, tmp_path: Path) -> None:
        assert await _bind(self._registry(tmp_path), "a1", "s1", _CONFIG) is True

    async def test_another_session_on_the_same_vni_is_refused(self, tmp_path: Path) -> None:
        # Setup would delete baivx4138 and its bridges before rebuilding them -- the devices of
        # whatever is already running on that VNI.
        registry = self._registry(tmp_path)
        await _bind(registry, "a1", "s1", _CONFIG)
        with pytest.raises(VniConflict, match="already held by session s1"):
            await _bind(registry, "a2", "s2", _CONFIG)

    async def test_the_same_session_from_another_agent_is_allowed(self, tmp_path: Path) -> None:
        # Two agents on one host sharing a session is the case this must NOT refuse.
        registry = self._registry(tmp_path)
        await _bind(registry, "a1", "s1", _CONFIG)
        assert await _bind(registry, "a2", "s1", _CONFIG) is True

    async def test_the_same_session_under_a_new_configuration_is_refused(
        self, tmp_path: Path
    ) -> None:
        registry = self._registry(tmp_path)
        await _bind(registry, "a1", "s1", _CONFIG)
        with pytest.raises(VniConflict, match="different network configuration"):
            await _bind(registry, "a2", "s1", {**_CONFIG, "subnet": "10.128.9.0/24"})

    async def test_it_reports_an_existing_hold(self, tmp_path: Path) -> None:
        # What tells a caller to ADOPT the data plane rather than rebuild it.
        registry = self._registry(tmp_path)
        async with registry.binding(4138, "a1", "s1", config_digest(_CONFIG)) as first:
            assert first.already_held is False
        async with registry.binding(4138, "a2", "s1", config_digest(_CONFIG)) as second:
            assert second.already_held is True

    async def test_an_unusable_store_binds_nothing(self, tmp_path: Path) -> None:
        # Not "the VNI is free". A binding no other agent can read is not one.
        blocked = tmp_path / "blocked"
        blocked.write_text("not a directory")
        assert await _bind(VniRegistry(blocked / "vni"), "a1", "s1", _CONFIG) is False


class TestReleasing:
    async def test_the_last_holder_frees_it(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        assert await _release(registry, "a1", "s1", _CONFIG) is True
        assert await _bind(registry, "a2", "s2", _CONFIG) is True

    async def test_a_co_located_agent_keeps_it_bound(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        await _bind(registry, "a2", "s1", _CONFIG)
        assert await _release(registry, "a1", "s1", _CONFIG) is False
        with pytest.raises(VniConflict):
            await _bind(registry, "a3", "s2", _CONFIG)


class TestPruning:
    async def test_a_binding_with_nobody_behind_it_is_dropped(self, tmp_path: Path) -> None:
        # A crash between binding a VNI and tearing it down otherwise refuses that VNI to every
        # later session on this node.
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        assert await registry.prune("a1", []) == 1
        assert await _bind(registry, "a2", "s2", _CONFIG) is True

    async def test_a_live_binding_survives(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        assert await registry.prune("a1", [("s1", config_digest(_CONFIG))]) == 0
        with pytest.raises(VniConflict):
            await _bind(registry, "a2", "s2", _CONFIG)

    async def test_another_agents_binding_is_not_ours_to_drop(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        assert await registry.prune("a2", []) == 0


class TestHolders:
    async def test_it_names_the_agent_the_session_and_the_configuration(
        self, tmp_path: Path
    ) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        assert await registry.holders(4138) == frozenset({
            VniHolder(agent_id="a1", session_id="s1", digest=config_digest(_CONFIG))
        })

    def test_a_malformed_claim_is_ignored_rather_than_trusted(self) -> None:
        assert VniHolder.parse("no-separator") is None
        assert VniHolder.parse("a1/s1") is None
