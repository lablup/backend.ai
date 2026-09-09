"""Wire round-trips for the privnet request protocol.

A field that the dataclass carries and the decoder accepts still reaches the privnet as None
unless `encode` puts it on the wire, and nothing above this layer can tell the difference: the
request succeeds, the privnet acts on an empty value, and the caller sees no error. Measured
exactly that way -- ENSURE_SECURITY was sent every reconcile with the session's peers, the privnet
received none of them, so it rebuilt no ownership and teardown left that node's SAs and policies
behind while its two peers cleaned up completely.
"""

import json
from typing import Any

import pytest

from ai.backend.agent.network.privnet.protocol import (
    PROTOCOL_VERSION,
    PrivNetOp,
    PrivNetRequest,
    PrivNetResponse,
    ProtocolError,
)


def _round_trip(request: PrivNetRequest) -> PrivNetRequest:
    return PrivNetRequest.decode(request.encode())


class TestRequestRoundTrip:
    def test_every_field_a_request_carries_survives_the_wire(self) -> None:
        # Guards the whole struct rather than one field, so a new field added to the dataclass and
        # the decoder but not to `encode` fails here instead of in production.
        request = PrivNetRequest(
            op=PrivNetOp.ATTACH_CONTAINER,
            session_id="s1",
            container_id="c1",
            network_config={"backend": "vxlan", "vni": 4097},
            vtep_ip="10.0.0.2",
            ip="10.128.5.7",
            mac="02:42:0a:80:05:07",
            local_ip="10.64.0.3",
            vteps=("10.0.0.2", "10.0.0.3"),
            ports=((30001, 2200, None, "tcp"),),
            dns_port=53535,
            cgroup_pid=4242,
            cgroup_limits={"memory.max": "1024"},
        )

        assert _round_trip(request) == request

    def test_the_peer_list_reaches_the_privnet(self) -> None:
        request = PrivNetRequest(
            op=PrivNetOp.ENSURE_SECURITY,
            session_id="s1",
            vteps=("10.0.0.2", "10.0.0.3"),
        )

        assert _round_trip(request).vteps == ("10.0.0.2", "10.0.0.3")

    def test_an_absent_peer_list_stays_absent(self) -> None:
        request = PrivNetRequest(op=PrivNetOp.ENSURE_SECURITY, session_id="s1")

        assert _round_trip(request).vteps is None

    def test_an_empty_peer_list_is_not_confused_with_an_absent_one(self) -> None:
        # A session that legitimately has no peers yet, versus one whose list never made it.
        request = PrivNetRequest(op=PrivNetOp.ENSURE_SECURITY, session_id="s1", vteps=())

        assert _round_trip(request).vteps == ()

    @pytest.mark.parametrize("bad", ["10.0.0.2", [1, 2], [None], {"a": "b"}])
    def test_a_malformed_peer_list_is_refused(self, bad: Any) -> None:
        # It arrives via the agent, so it is untrusted like every other field.
        payload = json.dumps({
            "op": str(PrivNetOp.ENSURE_SECURITY),
            "session_id": "s1",
            "vteps": bad,
        }).encode()

        with pytest.raises(ProtocolError):
            PrivNetRequest.decode(payload)


class TestTheProtocolVersion:
    """A caller tells "this daemon does not know that verb" from "it said no" by the version, not
    by the shape of an error string."""

    def test_it_roundtrips(self) -> None:
        resp = PrivNetResponse(ok=True, version=PROTOCOL_VERSION)
        assert PrivNetResponse.decode(resp.encode()).version == PROTOCOL_VERSION

    def test_a_response_without_one_decodes_as_absent(self) -> None:
        assert PrivNetResponse.decode(PrivNetResponse(ok=True).encode()).version is None

    def test_a_non_integer_version_is_refused(self) -> None:
        with pytest.raises(ProtocolError):
            PrivNetResponse.decode(b'{"ok": true, "version": "2"}')

    def test_problems_roundtrip(self) -> None:
        resp = PrivNetResponse(ok=True, problems={"privnet:session:s1": "no journal record"})
        assert PrivNetResponse.decode(resp.encode()).problems == {
            "privnet:session:s1": "no journal record"
        }

    def test_malformed_problems_are_refused(self) -> None:
        with pytest.raises(ProtocolError):
            PrivNetResponse.decode(b'{"ok": true, "problems": {"a": 1}}')


class TestForwardsOnTheWire:
    """LIST_PORTS is how an agent behind a privnet learns what is published on its node, and the
    reclaim decides on two of the fields alone: who installed the rule and when. Dropping them here
    is invisible -- the response is well formed and every port is listed -- and every stale rule
    then becomes permanent, because "no owner recorded" means "not mine to remove"."""

    def test_the_owner_and_the_install_time_survive_the_wire(self) -> None:
        resp = PrivNetResponse(ok=True, forwards=(("c1", 30001, "172.30.0.5", 8070, "i-dk-1", 42),))
        assert PrivNetResponse.decode(resp.encode()).forwards == (
            ("c1", 30001, "172.30.0.5", 8070, "i-dk-1", 42),
        )

    def test_a_daemon_that_still_sends_four_fields_decodes_as_unowned(self) -> None:
        """Older privnet, newer agent. Unknown owner leaves its rules alone, which is the safe way
        to be out of date -- a leaked port costs one port, a wrong reclaim costs a live session."""
        decoded = PrivNetResponse.decode(
            b'{"ok": true, "forwards": [["c1", 30001, "1.2.3.4", 80]]}'
        )
        assert decoded.forwards == (("c1", 30001, "1.2.3.4", 80, None, None),)

    def test_a_null_owner_or_time_is_accepted(self) -> None:
        decoded = PrivNetResponse.decode(
            b'{"ok": true, "forwards": [["c1", 30001, "1.2.3.4", 80, null, null]]}'
        )
        assert decoded.forwards == (("c1", 30001, "1.2.3.4", 80, None, None),)

    @pytest.mark.parametrize(
        "raw",
        [
            b'{"ok": true, "forwards": [["c1", 30001, "1.2.3.4", 80, 7, 42]]}',
            b'{"ok": true, "forwards": [["c1", 30001, "1.2.3.4", 80, "i-dk-1", "42"]]}',
            b'{"ok": true, "forwards": [["c1", 30001, "1.2.3.4", 80, "i-dk-1"]]}',
        ],
    )
    def test_a_malformed_entry_is_refused(self, raw: bytes) -> None:
        with pytest.raises(ProtocolError):
            PrivNetResponse.decode(raw)
