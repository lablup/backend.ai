"""Node-wide ownership of a VNI.

The privnet does not trust the agent with privileged networking, but it did take the network
configuration at face value: any VNI the agent named became the VNI whose `baivx*`, `baibr*` and
LOCAL bridge devices setup deletes and rebuilds. These pin the binding that stops one agent's
declaration from reaching into another session's data plane.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.network.pair_journal import PairJournal
from ai.backend.agent.network.vni_registry import (
    VniConflict,
    VniHolder,
    VniRegistry,
    VniStillBound,
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


async def _bind(
    registry: VniRegistry, agent: str, session: str, config: dict[str, Any], *, built: bool = True
) -> bool:
    """Reserve the VNI and, unless the caller is modelling a setup that died partway, record that
    its devices were actually built."""
    async with registry.binding(int(config["vni"]), agent, session, config_digest(config)) as b:
        if b.recorded and built:
            b.mark_built()
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

    async def test_it_reports_a_data_plane_that_already_exists(self, tmp_path: Path) -> None:
        # What tells a caller to ADOPT the data plane rather than rebuild it.
        registry = self._registry(tmp_path)
        async with registry.binding(4138, "a1", "s1", config_digest(_CONFIG)) as first:
            assert first.already_held is False
            first.mark_built()
        async with registry.binding(4138, "a2", "s1", config_digest(_CONFIG)) as second:
            assert second.already_held is True

    async def test_a_reservation_alone_is_not_a_data_plane(self, tmp_path: Path) -> None:
        # The claim is written BEFORE the devices. A setup that died in the middle -- and failed
        # to clean up after itself -- leaves one behind, and adopting it adopts nothing: the next
        # setup would report success over a session with no bridge and no VXLAN device.
        registry = self._registry(tmp_path)
        await _bind(registry, "a1", "s1", _CONFIG, built=False)
        async with registry.binding(4138, "a2", "s1", config_digest(_CONFIG)) as second:
            assert second.already_held is False

    async def test_an_abandoned_reservation_frees_the_vni(self, tmp_path: Path) -> None:
        registry = self._registry(tmp_path)
        async with registry.binding(4138, "a1", "s1", config_digest(_CONFIG)) as first:
            first.abandon()
        assert await _bind(registry, "a2", "s2", _CONFIG) is True

    async def test_a_reservation_still_conflicts_with_another_session(self, tmp_path: Path) -> None:
        # Two agents must not build the same VNI at once, whether or not either has finished.
        registry = self._registry(tmp_path)
        await _bind(registry, "a1", "s1", _CONFIG, built=False)
        with pytest.raises(VniConflict):
            await _bind(registry, "a2", "s2", _CONFIG)

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

    async def test_a_reservation_with_nobody_behind_it_is_dropped_too(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG, built=False)
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
            VniHolder(agent_id="a1", session_id="s1", digest=config_digest(_CONFIG), built=True)
        })

    async def test_it_says_whether_the_data_plane_was_built(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG, built=False)
        assert [holder.built for holder in await registry.holders(4138)] == [False]

    def test_a_malformed_claim_is_ignored_rather_than_trusted(self) -> None:
        assert VniHolder.parse("no-separator") is None
        assert VniHolder.parse("a1/s1") is None
        assert VniHolder.parse("a1/nonsense#s1#abc") is None


class TestAClaimThisAgentCannotRead:
    """A claim whose owner or state cannot be made out still means somebody holds the VNI. Skipping
    it is how the registry reports the VNI as free and setup deletes the devices behind it -- and
    an agent started with no id writes exactly such a claim, as does the claim format of an
    earlier release."""

    async def test_it_is_a_conflict_not_a_blank(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        # Rename the claim into a shape this version cannot parse, as an older one would have
        # written it.
        directory = tmp_path / "vni" / "vni4138"
        claim = next(f for f in directory.iterdir() if f.name != ".lock")
        claim.rename(directory / "s1#deadbeef")
        with pytest.raises(VniConflict, match="cannot read"):
            await _bind(registry, "a2", "s2", _CONFIG)

    async def test_an_agent_with_no_id_binds_nothing(self, tmp_path: Path) -> None:
        # Rather than write the unattributable claim in the first place.
        registry = VniRegistry(tmp_path / "vni")
        assert await _bind(registry, "", "s1", _CONFIG) is False
        assert await registry.holders(4138) == frozenset()


class TestTheClaimIsCommittedAfterTheTeardown:
    """`releasing` is held across the caller's teardown. If that teardown raises, the devices may
    still be up -- and a claim already gone lets the next session on this node take a VNI that is
    still carrying traffic."""

    async def test_a_failed_teardown_keeps_the_claim(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        with pytest.raises(RuntimeError):
            async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
                assert freed is True
                raise RuntimeError("ip link del failed")
        with pytest.raises(VniConflict):
            await _bind(registry, "a2", "s2", _CONFIG)

    async def test_a_successful_teardown_drops_it(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
            assert freed is True
        assert await _bind(registry, "a2", "s2", _CONFIG) is True

    async def test_the_answer_ignores_our_own_claim(self, tmp_path: Path) -> None:
        # "Would anyone be left?" -- not "is anyone here?", which is always yes while we are.
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        await _bind(registry, "a2", "s1", _CONFIG)
        async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
            assert freed is False


class TestHoldingNothingIsNotPermission:
    """`releasing` answers "may I delete this VNI's devices?". Computed as "is anything left after
    removing mine", it answers yes from an empty set -- so an agent that never had a claim, or
    whose claim something else removed, is handed permission to delete a live session's bridge and
    VXLAN device."""

    async def test_an_agent_with_no_claim_gets_no_answer(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        async with registry.releasing(4138, "a2", "s2", config_digest(_CONFIG)) as freed:
            assert freed is None

    async def test_an_empty_registry_gives_no_answer_either(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
            assert freed is None

    async def test_a_claim_removed_behind_our_back_gives_no_answer(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        directory = tmp_path / "vni" / "vni4138"
        for claim in directory.iterdir():
            if claim.name != ".lock":
                claim.unlink()
        async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
            assert freed is None


class TestAClaimThatWillNotGo:
    """The devices are gone and the claim is not. Logged and swallowed, the session's journal
    record goes with the teardown and the stale claim refuses that VNI to every later session
    until something else clears it."""

    async def test_it_is_raised_so_the_caller_keeps_the_record(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)

        directory = tmp_path / "vni" / "vni4138"
        with pytest.raises(VniStillBound, match="VNI 4138"):
            async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
                assert freed is True
                # The claim becomes unremovable while the caller is tearing the devices down.
                directory.chmod(0o500)
        directory.chmod(0o700)

    async def test_the_retry_finishes_the_job(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "vni")
        await _bind(registry, "a1", "s1", _CONFIG)
        directory = tmp_path / "vni" / "vni4138"
        with contextlib.suppress(VniStillBound):
            async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)):
                directory.chmod(0o500)
        directory.chmod(0o700)

        async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
            assert freed is True
        assert await _bind(registry, "a2", "s2", _CONFIG) is True


class TestABuiltClaimThatLandedIsCommitted:
    """`mark_built` writes the BUILT claim and then drops the reservation. Reporting the whole
    thing failed because only the second step did made the caller tear down a data plane the store
    had already vouched for -- after which the next setup adopted devices that no longer exist."""

    async def test_a_failed_tidy_up_does_not_undo_the_mark(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(PairJournal, "_remove_claim", lambda *args, **kwargs: False)
        registry = VniRegistry(tmp_path / "vni")
        async with registry.binding(4138, "a1", "s1", config_digest(_CONFIG)) as bound:
            assert bound.mark_built() is True

    async def test_the_leftover_reservation_conflicts_with_nobody(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with monkeypatch.context() as wedged:
            wedged.setattr(PairJournal, "_remove_claim", lambda *args, **kwargs: False)
            registry = VniRegistry(tmp_path / "vni")
            async with registry.binding(4138, "a1", "s1", config_digest(_CONFIG)) as bound:
                bound.mark_built()

        # It names the same session and the same configuration, so the data plane still reads as
        # built and a second agent on the same session still adopts.
        registry = VniRegistry(tmp_path / "vni")
        async with registry.binding(4138, "a2", "s1", config_digest(_CONFIG)) as second:
            assert second.already_held is True

    async def test_the_release_clears_both(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with monkeypatch.context() as wedged:
            wedged.setattr(PairJournal, "_remove_claim", lambda *args, **kwargs: False)
            registry = VniRegistry(tmp_path / "vni")
            async with registry.binding(4138, "a1", "s1", config_digest(_CONFIG)) as bound:
                bound.mark_built()

        registry = VniRegistry(tmp_path / "vni")
        async with registry.releasing(4138, "a1", "s1", config_digest(_CONFIG)) as freed:
            assert freed is True
        assert await registry.holders(4138) == frozenset()
