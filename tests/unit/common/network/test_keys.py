"""The keys core shares between the agent and the manager; pin the exact paths."""

from ai.backend.common.network.keys import agent_backend_key, agent_boot_key

_AID = "i-agent-1"


class TestCoreKeys:
    def test_agent_keys(self) -> None:
        assert agent_backend_key(_AID) == "network/agent/i-agent-1/backend"
        assert agent_boot_key(_AID) == "network/agent/i-agent-1/boot"
