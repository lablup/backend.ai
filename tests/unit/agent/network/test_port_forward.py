"""Host-port ingress (BEP-1078): the DNAT half of the LOCAL bridge's NAT."""

import inspect
from typing import Any, cast, override

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.network.port_forward import (
    ORPHAN_GRACE_SEC,
    PortForward,
    PortForwarder,
    dnat_rule,
    forwards_for,
    host_ports_of,
    install_args,
    is_orphaned,
    parse_forwards,
    remove_args,
)

_CID = "1f0f6f1a-0000-4000-8000-000000000001"
_FWD = PortForward(
    container_id=_CID, host_port=30001, container_ip="172.30.1.7", container_port=8070
)

# what `iptables -t nat -S PREROUTING` actually prints back
_SAVE_OUTPUT = f"""-P PREROUTING ACCEPT
-A PREROUTING -p tcp -m addrtype --dst-type LOCAL -m tcp --dport 30001 -m comment --comment "bai:{_CID}" -j DNAT --to-destination 172.30.1.7:8070
-A PREROUTING -p tcp -m addrtype --dst-type LOCAL -m tcp --dport 30002 -m comment --comment "bai:{_CID}" -j DNAT --to-destination 172.30.1.7:7681
-A PREROUTING -p tcp -m addrtype --dst-type LOCAL -m tcp --dport 30003 -m comment --comment "bai:other" -j DNAT --to-destination 172.30.1.9:8070
-A PREROUTING -d 169.254.169.254/32 -p tcp -m tcp --dport 80 -j DNAT --to-destination 127.0.0.1:50128
"""


class _Runner:
    def __init__(self, output: str = "") -> None:
        self.calls: list[list[str]] = []
        self._output = output

    async def __call__(self, argv: Any, *, check: bool = True) -> tuple[int, bytes, bytes]:
        self.calls.append(list(argv))
        return 0, self._output.encode(), b""

    def flat(self) -> str:
        return "\n".join(" ".join(c) for c in self.calls)


class _FailingRunner(_Runner):
    def __init__(self, fail_on_dport: str) -> None:
        super().__init__()
        self._fail_on = fail_on_dport

    @override
    async def __call__(self, argv: Any, *, check: bool = True) -> tuple[int, bytes, bytes]:
        argv = list(argv)
        self.calls.append(argv)
        if "-A" in argv and self._fail_on in argv:
            raise RuntimeError("iptables failed")
        return 0, b"", b""


class TestRuleBuilders:
    def test_publishes_on_both_prerouting_and_output(self) -> None:
        chains = [argv[argv.index("-A") + 1] for argv in install_args(_FWD)]
        # PREROUTING catches arriving traffic; OUTPUT catches the host's own connections, which
        # never traverse PREROUTING.
        assert chains == ["PREROUTING", "OUTPUT"]

    def test_rule_targets_the_container_address(self) -> None:
        argv = install_args(_FWD)[0]
        assert "--to-destination" in argv
        assert argv[argv.index("--to-destination") + 1] == "172.30.1.7:8070"
        assert argv[argv.index("--dport") + 1] == "30001"

    def test_rule_is_tagged_with_the_container_id(self) -> None:
        argv = install_args(_FWD)[0]
        assert argv[argv.index("--comment") + 1] == f"bai:{_CID}"

    def test_rule_only_matches_locally_destined_traffic(self) -> None:
        # this node forwards overlay traffic for its peers and makes its own outbound connections;
        # a port-only match would redirect both into a local container
        for argv in install_args(_FWD):
            assert argv[argv.index("--dst-type") + 1] == "LOCAL"

    def test_remove_mirrors_install_exactly(self) -> None:
        # a -D must match the installed rule body, or iptables refuses to delete it
        for add, delete in zip(install_args(_FWD), remove_args(_FWD), strict=True):
            assert add[:3] == ["iptables", "-t", "nat"]
            assert add[3] == "-A" and delete[3] == "-D"
            assert add[4:] == delete[4:]

    def test_forwards_for_pairs_host_container_ports_bind_ip_and_protocol(self) -> None:
        forwards = forwards_for(
            _CID,
            "172.30.1.7",
            [(30001, 8070, "127.0.0.1", "tcp"), (30002, 7681, None, "udp")],
        )
        assert [(f.host_port, f.container_port, f.host_ip, f.protocol) for f in forwards] == [
            (30001, 8070, "127.0.0.1", "tcp"),
            (30002, 7681, None, "udp"),
        ]
        assert host_ports_of(forwards) == [30001, 30002]

    def test_a_udp_port_emits_a_udp_dnat(self) -> None:
        forward = forwards_for(_CID, "172.30.1.7", [(30001, 8070, None, "udp")])[0]
        flat = " ".join(dnat_rule("PREROUTING", forward))
        assert "-p udp" in flat and "-p tcp" not in flat
        assert "--dport 30001" in flat


class TestParseFromIptables:
    """iptables is the record: no journal names the published ports."""

    def test_recovers_this_container_forwards(self) -> None:
        forwards = parse_forwards(_SAVE_OUTPUT, container_id=_CID)
        assert [(f.host_port, f.container_port) for f in forwards] == [(30001, 8070), (30002, 7681)]
        assert {f.container_ip for f in forwards} == {"172.30.1.7"}

    def test_ignores_other_containers(self) -> None:
        assert all(f.container_id == _CID for f in parse_forwards(_SAVE_OUTPUT, container_id=_CID))

    def test_ignores_foreign_dnat_rules(self) -> None:
        # e.g. the Docker Desktop metadata-service rule, which carries no bai: comment
        assert all(
            f.container_id.startswith(("1f0f", "other")) for f in parse_forwards(_SAVE_OUTPUT)
        )

    def test_recovers_every_container_when_unfiltered(self) -> None:
        assert host_ports_of(parse_forwards(_SAVE_OUTPUT)) == [30001, 30002, 30003]


class TestPortForwarder:
    async def test_install_applies_every_chain_for_every_port(self) -> None:
        runner = _Runner()
        await PortForwarder(runner).install(
            forwards_for(
                _CID, "172.30.1.7", [(30001, 8070, None, "tcp"), (30002, 7681, None, "tcp")]
            )
        )
        assert len(runner.calls) == 4  # 2 ports x 2 chains
        assert "PREROUTING" in runner.flat() and "OUTPUT" in runner.flat()

    async def test_a_failed_install_is_rolled_back(self) -> None:
        # otherwise a rule survives pointing at a container that never started. Both the fully
        # applied forward (30001) and the one that failed mid-apply (30002) are rolled back, each
        # across both chains — remove is idempotent, so covering the failed one is safe.
        runner = _FailingRunner("30002")
        forwarder = PortForwarder(runner)
        with pytest.raises(RuntimeError):
            await forwarder.install(
                forwards_for(
                    _CID, "172.30.1.7", [(30001, 8070, None, "tcp"), (30002, 7681, None, "tcp")]
                )
            )
        deletes = [c for c in runner.calls if "-D" in c]
        assert sorted(c[c.index("--dport") + 1] for c in deletes) == [
            "30001",
            "30001",
            "30002",
            "30002",
        ]

    async def test_a_partially_applied_forward_is_rolled_back(self) -> None:
        # install writes two chains per forward; if the OUTPUT insert fails after PREROUTING
        # succeeded, the in-progress forward must still be rolled back (else its PREROUTING rule
        # leaks, pointing at a container that never started)
        class _FailOnChain(_Runner):
            @override
            async def __call__(self, argv: Any, *, check: bool = True) -> tuple[int, bytes, bytes]:
                argv = list(argv)
                self.calls.append(argv)
                if "-A" in argv and "OUTPUT" in argv:
                    raise RuntimeError("iptables failed on OUTPUT")
                return 0, b"", b""

        runner = _FailOnChain()
        with pytest.raises(RuntimeError):
            await PortForwarder(runner).install(
                forwards_for(_CID, "172.30.1.7", [(30001, 8070, None, "tcp")])
            )
        # the PREROUTING rule that did get inserted must be deleted on rollback
        deletes = [c for c in runner.calls if "-D" in c and "PREROUTING" in c]
        assert [c[c.index("--dport") + 1] for c in deletes] == ["30001"]

    async def test_remove_container_drops_its_rules_and_returns_its_host_ports(self) -> None:
        runner = _Runner(_SAVE_OUTPUT)
        forwarder = PortForwarder(runner)

        released = await forwarder.remove_container(_CID)
        assert released == [30001, 30002]
        deletes = [c for c in runner.calls if "-D" in c]
        assert len(deletes) == 4  # 2 ports x 2 chains
        assert "bai:other" not in runner.flat()

    async def test_remove_of_an_unknown_container_is_a_noop(self) -> None:
        runner = _Runner(_SAVE_OUTPUT)
        assert await PortForwarder(runner).remove_container("never-seen") == []


class TestBindAddress:
    """S1/S2: a service is published on a chosen host address, not every one.

    A protected service (a storage node's ttyd shell) binds to loopback so it is not reachable
    off-node; an ordinary service binds to the operator's configured bind-host so kernel ports stay
    off interfaces the operator did not choose. Without this the DNAT matched --dst-type LOCAL, i.e.
    every local address, exposing both.
    """

    def _bound(self, host_ip: str | None) -> PortForward:
        return PortForward(
            container_id=_CID,
            host_port=30001,
            container_ip="172.30.1.7",
            container_port=8070,
            host_ip=host_ip,
        )

    def test_a_bound_service_matches_only_that_address(self) -> None:
        for argv in install_args(self._bound("127.0.0.1")):
            assert argv[argv.index("-d") + 1] == "127.0.0.1/32"
            assert "--dst-type" not in argv  # not the every-address form

    def test_an_unbound_service_matches_every_local_address(self) -> None:
        for argv in install_args(self._bound(None)):
            assert argv[argv.index("--dst-type") + 1] == "LOCAL"
            assert "-d" not in argv

    def test_0_0_0_0_binds_every_local_address_like_docker(self) -> None:
        # Docker treats HostIp "0.0.0.0" and "" identically (bind to all); the config's prod example
        # sets bind-host to "0.0.0.0". A literal ``-d 0.0.0.0/32`` matches no packet, so it must map
        # to the every-local-address form instead, or the published port is silently unreachable.
        for host_ip in ("0.0.0.0", ""):
            for argv in install_args(self._bound(host_ip)):
                assert argv[argv.index("--dst-type") + 1] == "LOCAL"
                assert "-d" not in argv

    def test_remove_of_a_bound_rule_mirrors_install(self) -> None:
        # A -D that dropped the -d would fail to delete the installed -d rule and leak it.
        fwd = self._bound("127.0.0.1")
        for add, delete in zip(install_args(fwd), remove_args(fwd), strict=True):
            assert add[4:] == delete[4:]

    def test_a_bound_rule_round_trips_through_iptables_parse(self) -> None:
        # remove_container lists the rules back from iptables and rebuilds -D from them, so the
        # parsed host_ip must equal the installed one or the removal silently leaks the rule.
        save = (
            f"-A PREROUTING -d 127.0.0.1/32 -p tcp -m tcp --dport 30001 "
            f'-m comment --comment "bai:{_CID}" -j DNAT --to-destination 172.30.1.7:8070'
        )
        (parsed,) = parse_forwards(save, container_id=_CID)
        assert parsed.host_ip == "127.0.0.1"
        assert parsed.host_port == 30001 and parsed.container_ip == "172.30.1.7"

    def test_an_unbound_rule_parses_back_to_none(self) -> None:
        (parsed,) = parse_forwards(_SAVE_OUTPUT.splitlines()[1], container_id=_CID)
        assert parsed.host_ip is None


class _Publisher:
    """A `PortPublisher` holding a fixed set of forwards, recording what is reclaimed."""

    def __init__(self, forwards: list[PortForward]) -> None:
        self._forwards = list(forwards)
        self.removed: list[str] = []

    async def install(self, forwards: Any) -> None:
        raise AssertionError("recovery must not install anything")

    async def remove_container(self, container_id: str) -> list[int]:
        self.removed.append(container_id)
        ports = [f.host_port for f in self._forwards if f.container_id == container_id]
        self._forwards = [f for f in self._forwards if f.container_id != container_id]
        return ports

    async def list_forwards(self, *, container_id: str | None = None) -> list[PortForward]:
        if container_id is None:
            return list(self._forwards)
        return [f for f in self._forwards if f.container_id == container_id]


async def _reclaim(publisher: _Publisher, live: set[str]) -> list[int]:
    """The decision `DockerAgent._reclaim_stale_port_forwards` makes, over an injected publisher.

    The method itself opens a Docker connection to learn the live set; what is worth pinning is
    which rules it decides to drop, so the set is supplied and the decision is exercised.
    """
    forwards = await publisher.list_forwards()
    stale = sorted({f.container_id for f in forwards} - live)
    reclaimed: list[int] = []
    for cid in stale:
        reclaimed.extend(await publisher.remove_container(cid))
    return reclaimed


class TestReclaimingRulesOfContainersThatAreGone:
    """iptables is the record, and nothing collected a rule whose container went away while the
    agent was down -- so they accumulated for the life of the host.

    They are not inert: the rule sits in nat PREROUTING and is matched *before* Docker's own DNAT
    for the same host port, so it wins and sends the connection to the address a dead session had.
    The port becomes a black hole for whatever is published on it next, and the agent's pool hands
    the low ports out again from the start on every restart -- so the same ports are poisoned
    every time. Measured on a live node: 72 stale rules over host ports 33100-33121, and every
    session that drew one failed to start while its container was healthy and reachable at its own
    address.
    """

    _DEAD = PortForward(
        container_id="dead-container",
        host_port=33100,
        container_ip="172.30.0.194",
        container_port=2000,
    )
    _LIVE = PortForward(
        container_id="live-container",
        host_port=33200,
        container_ip="172.30.1.5",
        container_port=2000,
    )

    async def test_a_dead_containers_rules_are_dropped(self) -> None:
        pub = _Publisher([self._DEAD])
        assert await _reclaim(pub, live=set()) == [33100]
        assert pub.removed == ["dead-container"]

    async def test_a_live_containers_rules_are_left_alone(self) -> None:
        """Including one that has not started yet: a container held at the creation gate needs its
        rules, and Docker still knows about it."""
        pub = _Publisher([self._LIVE])
        assert await _reclaim(pub, live={"live-container"}) == []
        assert pub.removed == []

    async def test_only_the_dead_ones_go_when_both_are_present(self) -> None:
        pub = _Publisher([self._DEAD, self._LIVE])
        assert await _reclaim(pub, live={"live-container"}) == [33100]
        assert [f.container_id for f in await pub.list_forwards()] == ["live-container"]

    async def test_every_port_a_dead_container_held_comes_back(self) -> None:
        """A kernel publishes seven ports; leaving any behind leaves that one poisoned."""
        dead = [
            PortForward(
                container_id="dead-container",
                host_port=33100 + i,
                container_ip="172.30.0.194",
                container_port=p,
            )
            for i, p in enumerate((2000, 2001, 2200, 7681, 8070, 8090, 8180))
        ]
        pub = _Publisher(dead)
        assert await _reclaim(pub, live=set()) == list(range(33100, 33107))

    async def test_startup_reclaims_before_it_serves(self) -> None:
        """Order is the invariant: the reclaim has to happen while the agent is coming up, before
        it can be handed work that draws one of the poisoned ports."""
        source = inspect.getsource(AbstractAgent.scan_running_kernels)
        assert "_reclaim_stale_port_forwards()" in source, (
            "startup no longer reclaims the rules of containers that are gone, so the low host"
            " ports stay black holes and the first sessions after a restart cannot start"
        )
        assert source.index("_reclaim_stale_port_forwards()") < source.index(
            "_defer_ports_the_host_still_holds()"
        ), "the reclaim gives ports back, so it has to run before the pool decides what to hold"

    def test_every_backend_gets_it_not_just_docker(self) -> None:
        """The rules are shared machinery: whoever publishes through `port_forward` leaks the same
        way, and a backend added later would have to remember to do this. So the reclaim lives on
        `AbstractAgent`, and a backend only says whether it publishes host ports at all."""
        assert hasattr(AbstractAgent, "_reclaim_stale_port_forwards")
        assert AbstractAgent.port_publisher(cast(Any, object())) is None, (
            "a backend that publishes no host ports must opt out by default, not crash"
        )
        assert "port_publisher" in inspect.getsource(DockerAgent)


class TestTheTagRecordsWhenAsWellAsWho:
    """The comment is the record: `bai:<container_id>:<unix seconds>`. The id answers whose rule it
    is, the time answers whether it has been orphaned long enough to act on."""

    def test_a_new_rule_carries_all_three(self) -> None:
        [fwd] = forwards_for(
            _CID, "172.30.1.7", [(30001, 8070, None, "tcp")], owner_agent_id="i-dk-104"
        )
        assert fwd.created_at is not None
        rule = " ".join(dnat_rule("PREROUTING", fwd))
        assert f"bai:i-dk-104:{_CID}:{fwd.created_at}" in rule

    def test_every_older_tag_form_still_parses(self) -> None:
        """Nothing a previous agent wrote may become unremovable -- that is the leak itself."""
        base = (
            "-A PREROUTING -p tcp -m addrtype --dst-type LOCAL -m tcp --dport 30001 "
            '-m comment --comment "{tag}" -j DNAT --to-destination 172.30.1.7:8070'
        )
        [old] = parse_forwards(base.format(tag=f"bai:{_CID}"))
        assert (old.container_id, old.owner_agent_id, old.created_at) == (_CID, None, None)
        [timed] = parse_forwards(base.format(tag=f"bai:{_CID}:1788900000"))
        assert (timed.container_id, timed.owner_agent_id, timed.created_at) == (
            _CID,
            None,
            1788900000,
        )
        [full] = parse_forwards(base.format(tag=f"bai:i-dk-104:{_CID}:1788900000"))
        assert (full.container_id, full.owner_agent_id, full.created_at) == (
            _CID,
            "i-dk-104",
            1788900000,
        )

    def test_it_parses_back_to_the_same_rule(self) -> None:
        """`-D` regenerates the rule body from what was parsed, so a timestamp that did not round
        trip would leave a rule that cannot be removed -- the very leak this is against."""
        [fwd] = forwards_for(
            _CID, "172.30.1.7", [(30001, 8070, None, "tcp")], owner_agent_id="i-dk-104"
        )
        line = "-A " + " ".join(dnat_rule("PREROUTING", fwd))
        [parsed] = parse_forwards(line)
        assert parsed == fwd
        assert dnat_rule("PREROUTING", parsed) == dnat_rule("PREROUTING", fwd)

    def test_a_rule_written_before_timestamps_still_parses(self) -> None:
        """Rules from an older agent carry the id alone. They must stay removable by tag."""
        line = (
            "-A PREROUTING -p tcp -m addrtype --dst-type LOCAL -m tcp --dport 30001 "
            f'-m comment --comment "bai:{_CID}" -j DNAT --to-destination 172.30.1.7:8070'
        )
        [parsed] = parse_forwards(line)
        assert parsed.container_id == _CID
        assert parsed.created_at is None


class TestWhenAnOrphanedRuleMayBeTaken:
    """ "Its container is not in Docker" is not on its own a safe reason to delete a rule: the rule
    is installed a moment before the container becomes visible, and a sweep landing in that window
    would cut a starting kernel off from its own published ports. The age is what closes that."""

    _OWNER = "i-dk-104"

    def _fwd(self, created_at: int | None, owner: str | None = _OWNER) -> PortForward:
        return PortForward(
            container_id="c1",
            host_port=33100,
            container_ip="172.30.0.194",
            container_port=2000,
            owner_agent_id=owner,
            created_at=created_at,
        )

    def test_a_live_containers_rule_is_never_taken(self) -> None:
        assert not is_orphaned(self._fwd(created_at=0), {"c1"}, now=1e9, owner_agent_id=self._OWNER)

    def test_a_freshly_installed_rule_is_left_alone(self) -> None:
        now = 1_000_000.0
        assert not is_orphaned(
            self._fwd(created_at=int(now) - 1), set(), now=now, owner_agent_id=self._OWNER
        )

    def test_it_is_taken_once_the_grace_has_passed(self) -> None:
        now = 1_000_000.0
        assert is_orphaned(
            self._fwd(created_at=int(now - ORPHAN_GRACE_SEC)),
            set(),
            now=now,
            owner_agent_id=self._OWNER,
        )

    def test_a_rule_with_no_timestamp_is_old_by_definition(self) -> None:
        """It was written by an agent that predates the stamp, so its process is gone."""
        assert is_orphaned(self._fwd(created_at=None), set(), now=1e9, owner_agent_id=self._OWNER)

    def test_another_agents_rule_is_never_touched(self) -> None:
        """The decisive one for a node running more than one runtime. `live_container_ids` is one
        runtime's listing, so a docker agent cannot see a containerd/podman/apptainer container --
        and a rule for one would look orphaned to it. Reclaiming that would take a live kernel's
        published ports away."""
        assert not is_orphaned(
            self._fwd(created_at=0, owner="i-ctrd-104"),
            set(),
            now=1e9,
            owner_agent_id=self._OWNER,
        )

    def test_a_rule_with_no_owner_recorded_is_left_alone(self) -> None:
        """Written before the owner was recorded: nobody can prove it is dead, and leaking a port
        is cheaper than cutting off a session that is still running."""
        assert not is_orphaned(
            self._fwd(created_at=0, owner=None), set(), now=1e9, owner_agent_id=self._OWNER
        )

    def test_the_grace_is_long_enough_to_cover_a_creation_but_not_a_session(self) -> None:
        """Pinned so neither end drifts: too short and a starting kernel loses its ports, too long
        and the black hole outlives the port pool's own reuse cooldown."""
        assert 5.0 <= ORPHAN_GRACE_SEC <= 300.0


class TestAnUnownedRuleIsReported:
    """It is not reclaimed -- `is_orphaned` refuses it, because an unowned rule may belong to a
    co-located agent whose containers this runtime cannot see. But nothing this code writes is
    untagged, so finding one at startup means an older build left it behind, and it will hold its
    host port for the life of the node. Measured: 34 on one node, discovered months later as ports
    that would not bind, with nothing on the node saying why."""

    @staticmethod
    def _fwd(port: int, owner: str | None) -> PortForward:
        return PortForward(
            container_id="c",
            host_port=port,
            container_ip="172.30.0.2",
            container_port=2200,
            owner_agent_id=owner,
        )

    def _reported(self, forwards: list[PortForward]) -> list[int]:
        # `AbstractAgent` cannot be instantiated, and the method reads no attribute of it -- the
        # same shape the defer test next door uses. Asserted on the return rather than on the log
        # line, so the case does not depend on which handler another test left on the logger.
        return AbstractAgent._report_unowned_port_forwards(cast(Any, self), forwards)

    def test_every_unowned_rule_is_named(self) -> None:
        assert self._reported([
            self._fwd(33100, None),
            self._fwd(33200, "i-dk-1"),
            self._fwd(33101, None),
        ]) == [33100, 33101]

    def test_a_fully_owned_set_says_nothing(self) -> None:
        """The ordinary case, and it must stay quiet -- a warning on every startup is one nobody
        reads when it finally matters."""
        assert self._reported([self._fwd(33100, "i-dk-1"), self._fwd(33101, "i-dk-1")]) == []

    def test_the_reclaim_still_refuses_to_take_it(self) -> None:
        """The report does not change the decision; both must hold at once."""
        assert not is_orphaned(self._fwd(33100, None), set(), now=1e9, owner_agent_id="i-dk-1")

    def test_startup_reports_before_it_decides(self) -> None:
        source = inspect.getsource(AbstractAgent._reclaim_stale_port_forwards)
        assert "_report_unowned_port_forwards(" in source
