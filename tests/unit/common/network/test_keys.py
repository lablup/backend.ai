"""The etcd key layout is the manager<->agent contract; pin the exact paths so a change
on one side that forgets the other is caught here."""

from ai.backend.common.network.keys import (
    agent_backend_key,
    agent_caps_key,
    agent_vtep_key,
    endpoint_key,
    endpoints_prefix,
    member_key,
    members_prefix,
    session_ipam_key,
    session_meta_key,
    session_prefix,
)

_SID = "sess-1"
_AID = "i-agent-1"
_CID = "kern-1"


class TestSessionKeys:
    def test_session_prefix(self) -> None:
        assert session_prefix(_SID) == "network/session/sess-1/"

    def test_meta_key(self) -> None:
        assert session_meta_key(_SID) == "network/session/sess-1/meta"

    def test_members(self) -> None:
        assert members_prefix(_SID) == "network/session/sess-1/members/"
        assert member_key(_SID, _AID) == "network/session/sess-1/members/i-agent-1"

    def test_endpoints(self) -> None:
        assert endpoints_prefix(_SID) == "network/session/sess-1/endpoints/"
        assert endpoint_key(_SID, _CID) == "network/session/sess-1/endpoints/kern-1"

    def test_ipam_key(self) -> None:
        assert session_ipam_key(_SID, "10.128.0.2") == "network/session/sess-1/ipam/10.128.0.2"

    def test_member_key_nests_under_members_prefix(self) -> None:
        assert member_key(_SID, _AID).startswith(members_prefix(_SID))
        assert endpoint_key(_SID, _CID).startswith(endpoints_prefix(_SID))


class TestAgentKeys:
    def test_agent_keys(self) -> None:
        assert agent_caps_key(_AID) == "network/agent/i-agent-1/caps"
        assert agent_backend_key(_AID) == "network/agent/i-agent-1/backend"
        assert agent_vtep_key(_AID) == "network/agent/i-agent-1/vtep"
