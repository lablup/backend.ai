"""The data-plane backends are a plugin seam, not an import (BEP-1079).

The session network drives a backend through `AbstractNetworkAgentPluginV2`. If the core reaches
for a concrete backend by name -- an import of the vxlan class, of the privileged helper's daemon
-- the seam exists only on paper: the package can no longer be shipped, versioned or left out
separately, and a node with no backend installed fails at import instead of simply serving no
cluster-network session.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ai.backend.agent.network import registry as registry_mod
from ai.backend.agent.network import session_network
from ai.backend.agent.network.registry import BackendSpec, load_backends

#: What a node's own facts look like; the store is a stand-in because no real backend is built.
_SPEC = BackendSpec(uplink="eth0", local_subnets=MagicMock(), agent_id="i-node")


def _entrypoint(name: str, *, broken: bool = False) -> MagicMock:
    entrypoint = MagicMock()
    entrypoint.name = name
    if broken:
        entrypoint.load.return_value.create.side_effect = RuntimeError("no such device")
    else:
        entrypoint.load.return_value.create.return_value = MagicMock(name=f"{name}-backend")
    return entrypoint


class TestWhatTheRegistryLoads:
    def test_each_declared_backend_is_built_from_the_nodes_facts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vxlan, bridge = _entrypoint("vxlan"), _entrypoint("bridge")
        monkeypatch.setattr(registry_mod, "scan_entrypoints", lambda group: iter((vxlan, bridge)))
        assert set(load_backends(_SPEC)) == {"vxlan", "bridge"}
        # Built through `create`, which is the contract a backend implements -- never through a
        # constructor the core would have to know the shape of.
        vxlan.load.return_value.create.assert_called_once_with(_SPEC)

    def test_the_group_scanned_is_the_declared_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: list[str] = []

        def _scan(group: str) -> object:
            seen.append(group)
            return iter(())

        monkeypatch.setattr(registry_mod, "scan_entrypoints", _scan)
        load_backends(_SPEC)
        assert seen == [registry_mod.BACKEND_PLUGIN_GROUP]

    def test_a_backend_that_cannot_be_built_is_left_out(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One broken backend must not take the others with it: the node then does not advertise
        it, which is what keeps a session from being placed where it cannot be served."""
        monkeypatch.setattr(
            registry_mod,
            "scan_entrypoints",
            lambda group: iter((_entrypoint("broken", broken=True), _entrypoint("good"))),
        )
        assert set(load_backends(_SPEC)) == {"good"}

    def test_nothing_installed_is_an_empty_result_not_an_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A node with no backend serves no cluster-network session, which is a placement fact the
        # manager already reads from the capability record -- not a reason to fail startup.
        monkeypatch.setattr(registry_mod, "scan_entrypoints", lambda group: iter(()))
        assert load_backends(_SPEC) == {}


class TestTheSeamItself:
    def test_the_session_network_names_no_backend(self) -> None:
        """The factory must reach the backends through the registry alone.

        Checked on the source because that is where the regression appears: an import added back
        for convenience works on every machine that happens to have the backend installed.
        """
        source = Path(session_network.__file__).read_text()
        offending = [
            line for line in source.splitlines() if "import" in line and "network.backends" in line
        ]
        assert offending == [], offending
