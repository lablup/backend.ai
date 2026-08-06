"""Unit tests for the privnet cluster DNS resolver (BEP-1062).

The resolve logic is pure: a fake name source and a fake forwarder stand in for etcd and the
upstream so a query can be answered/forwarded without a socket or the network.
"""

from __future__ import annotations

from collections.abc import Mapping

import dns.asyncquery
import dns.exception
import dns.flags
import dns.message
import dns.name
import dns.rcode
import dns.rdataclass
import dns.rdatatype
import dns.rrset
import pytest

from ai.backend.agent.network.privnet.resolver import (
    ClusterResolver,
    Forwarder,
    make_upstream_forwarder,
)


class _FakeNames:
    def __init__(self, mapping: Mapping[str, str]) -> None:
        self._mapping = dict(mapping)

    def resolve_name(self, hostname: str) -> str | None:
        return self._mapping.get(hostname)


def _forwarded_marker() -> Forwarder:
    """A forwarder that tags its response with REFUSED so a test can prove forwarding happened."""

    async def forward(query: dns.message.Message) -> dns.message.Message:
        resp = dns.message.make_response(query)
        resp.set_rcode(dns.rcode.REFUSED)
        return resp

    return forward


def _resolver(names: Mapping[str, str]) -> ClusterResolver:
    return ClusterResolver(_FakeNames(names), _forwarded_marker())


class TestClusterResolve:
    async def test_a_cluster_name_gets_an_authoritative_a_record(self) -> None:
        resolver = _resolver({"sub1": "10.128.7.1"})
        resp = await resolver.resolve(dns.message.make_query("sub1.", "A"))

        assert resp.rcode() == dns.rcode.NOERROR
        assert resp.flags & dns.flags.AA  # authoritative for a name we own
        assert len(resp.answer) == 1
        rrset = resp.answer[0]
        assert rrset.rdtype == dns.rdatatype.A
        assert str(rrset[0]) == "10.128.7.1"

    async def test_name_matching_is_case_insensitive(self) -> None:
        resolver = _resolver({"main1": "10.128.7.2"})
        resp = await resolver.resolve(dns.message.make_query("MAIN1.", "A"))
        assert str(resp.answer[0][0]) == "10.128.7.2"

    async def test_a_known_name_queried_for_aaaa_is_authoritative_nodata(self) -> None:
        # A name we own but with no AAAA: an empty NOERROR (NODATA), NOT a forward or NXDOMAIN, so
        # the client does not chase a name we are authoritative for out to the upstream resolver.
        resolver = _resolver({"sub1": "10.128.7.1"})
        resp = await resolver.resolve(dns.message.make_query("sub1.", "AAAA"))

        assert resp.rcode() == dns.rcode.NOERROR
        assert resp.flags & dns.flags.AA
        assert len(resp.answer) == 0

    async def test_an_unknown_name_is_forwarded(self) -> None:
        resolver = _resolver({"sub1": "10.128.7.1"})
        resp = await resolver.resolve(dns.message.make_query("pypi.org.", "A"))
        assert resp.rcode() == dns.rcode.REFUSED  # the forwarder marker: not answered locally

    async def test_a_non_internet_class_query_is_forwarded(self) -> None:
        resolver = _resolver({"sub1": "10.128.7.1"})
        query = dns.message.make_query("sub1.", "A", rdclass=dns.rdataclass.CH)
        resp = await resolver.resolve(query)
        assert resp.rcode() == dns.rcode.REFUSED

    async def test_a_multi_question_query_is_forwarded(self) -> None:
        resolver = _resolver({"sub1": "10.128.7.1"})
        query = dns.message.make_query("sub1.", "A")
        query.question.append(
            dns.rrset.RRset(dns.name.from_text("main1."), dns.rdataclass.IN, dns.rdatatype.A)
        )
        resp = await resolver.resolve(query)
        assert resp.rcode() == dns.rcode.REFUSED


class TestUpstreamForwarder:
    async def test_returns_the_first_upstream_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        answer = dns.message.make_query("x.", "A")

        async def fake_udp(
            query: dns.message.Message, server: str, timeout: float
        ) -> dns.message.Message:
            return answer

        monkeypatch.setattr(dns.asyncquery, "udp", fake_udp)
        forward = make_upstream_forwarder(["1.1.1.1"])
        assert await forward(dns.message.make_query("x.", "A")) is answer

    async def test_falls_through_to_the_next_upstream(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        answer = dns.message.make_query("x.", "A")
        tried: list[str] = []

        async def fake_udp(
            query: dns.message.Message, server: str, timeout: float
        ) -> dns.message.Message:
            tried.append(server)
            if server == "1.1.1.1":
                raise dns.exception.Timeout
            return answer

        monkeypatch.setattr(dns.asyncquery, "udp", fake_udp)
        forward = make_upstream_forwarder(["1.1.1.1", "2.2.2.2"])
        assert await forward(dns.message.make_query("x.", "A")) is answer
        assert tried == ["1.1.1.1", "2.2.2.2"]

    async def test_servfails_when_all_upstreams_fail(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # SERVFAIL (not NXDOMAIN) so the stub resolver can still try its next configured nameserver.
        async def fail(
            query: dns.message.Message, server: str, timeout: float
        ) -> dns.message.Message:
            raise dns.exception.Timeout

        monkeypatch.setattr(dns.asyncquery, "udp", fail)
        forward = make_upstream_forwarder(["1.1.1.1", "2.2.2.2"])
        resp = await forward(dns.message.make_query("x.", "A"))
        assert resp.rcode() == dns.rcode.SERVFAIL
