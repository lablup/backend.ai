"""Host-port ingress (BEP-1062): the DNAT half of the LOCAL bridge's NAT."""

from typing import Any, override

import pytest

from ai.backend.agent.network.port_forward import (
    PortForward,
    PortForwarder,
    forwards_for,
    host_ports_of,
    install_args,
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

    def test_forwards_for_pairs_host_container_ports_and_bind_ip(self) -> None:
        forwards = forwards_for(
            _CID, "172.30.1.7", [(30001, 8070, "127.0.0.1"), (30002, 7681, None)]
        )
        assert [(f.host_port, f.container_port, f.host_ip) for f in forwards] == [
            (30001, 8070, "127.0.0.1"),
            (30002, 7681, None),
        ]
        assert host_ports_of(forwards) == [30001, 30002]


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
            forwards_for(_CID, "172.30.1.7", [(30001, 8070, None), (30002, 7681, None)])
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
                forwards_for(_CID, "172.30.1.7", [(30001, 8070, None), (30002, 7681, None)])
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
                forwards_for(_CID, "172.30.1.7", [(30001, 8070, None)])
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
