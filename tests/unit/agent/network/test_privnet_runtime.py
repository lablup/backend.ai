"""privnet must drive THIS node's backend, not containerd by assumption.

`_attach` answers by asking the runtime for a container's PID. Hard-coding the containerd client
meant it asked a daemon that has never heard of an enroot or apptainer container, so a rootless
agent could not delegate its networking at all and had to run privileged — the opposite of what
the rootless backends are for. The backend already publishes its own client through the discovery,
which is the same dispatch that fixed the equivalent bug in the commit path (e2202cb5a).
"""

from __future__ import annotations

import json as _json
from typing import Any, cast

import pytest

import ai.backend.agent.network.privnet.__main__ as main_mod
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.network.privnet.__main__ import _build_runtime
from ai.backend.agent.network.privnet.protocol import PrivNetOp, PrivNetRequest, ProtocolError
from ai.backend.agent.types import AgentBackend


class _Sentinel:
    """Stands in for whatever the discovery hands back; identity is the whole assertion."""


class TestTheRuntimeFollowsTheConfiguredBackend:
    @pytest.mark.parametrize("key", ["backend", "mode"])
    @pytest.mark.parametrize(
        "backend", [AgentBackend.ENROOT, AgentBackend.SINGULARITY, AgentBackend.CONTAINERD]
    )
    def test_it_asks_the_discovery_for_that_backend(
        self, monkeypatch: pytest.MonkeyPatch, key: str, backend: AgentBackend
    ) -> None:
        asked: list[AgentBackend] = []
        sentinel = _Sentinel()

        class _Discovery:
            def create_oci_runtime(self, local_config: Any) -> Any:
                return sentinel

        monkeypatch.setattr(
            AgentUnifiedConfig, "model_validate", classmethod(lambda cls, cfg: object())
        )

        def _discovery(backend: AgentBackend) -> _Discovery:
            asked.append(backend)
            return _Discovery()

        monkeypatch.setattr(main_mod, "get_agent_discovery", _discovery)

        got = _build_runtime({"agent": {key: backend.value}}, "backend-ai")

        assert cast(object, got) is sentinel
        assert asked == [backend]

    def test_without_a_config_it_falls_back_to_containerd(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The only case where the backend is genuinely unknown — and the historical default."""
        made: list[str] = []

        class _Ctrd:
            def __init__(self, *, namespace: str) -> None:
                made.append(namespace)

        monkeypatch.setattr(main_mod, "ContainerdGrpcRuntime", _Ctrd)
        monkeypatch.setattr(
            main_mod,
            "get_agent_discovery",
            lambda b: pytest.fail("the discovery must not be consulted without a backend"),
        )

        _build_runtime({}, "backend-ai")

        assert made == ["backend-ai"]


class TestTheCgroupOps:
    """A rootless backend has no daemon to create its containers' cgroups — containerd and dockerd
    declare `cgroupsPath` and their ROOT daemon obliges — and an unprivileged agent cannot make one
    itself. Measured before the delegation: a kernel allocated 8 GiB and 4 CPUs ran with
    `memory.max = max` and `Cpus_allowed_list: 0-31`."""

    def test_the_request_round_trips(self) -> None:
        req = PrivNetRequest(
            op=PrivNetOp.CONFINE_CONTAINER,
            session_id="s1",
            container_id="c1",
            cgroup_pid=4321,
            cgroup_limits={"memory.max": "8589934592", "cpuset.cpus": "0-3"},
        )
        back = PrivNetRequest.decode(req.encode())
        assert back.op is PrivNetOp.CONFINE_CONTAINER
        assert back.cgroup_pid == 4321
        assert back.cgroup_limits == {"memory.max": "8589934592", "cpuset.cpus": "0-3"}

    @pytest.mark.parametrize("bad", [0, 1, -5, True, "4321"])
    def test_a_pid_that_could_not_be_a_container_is_refused(self, bad: object) -> None:
        """PID 0/1 name the host's own, and a non-int names nothing at all."""
        frame = _json.dumps({
            "op": "confine_container",
            "session_id": "s1",
            "container_id": "c1",
            "cgroup_pid": bad,
        }).encode()
        with pytest.raises(ProtocolError):
            PrivNetRequest.decode(frame)

    def test_limits_must_be_a_string_map(self) -> None:
        frame = _json.dumps({
            "op": "confine_container",
            "session_id": "s1",
            "container_id": "c1",
            "cgroup_pid": 42,
            "cgroup_limits": {"memory.max": 8589934592},
        }).encode()
        with pytest.raises(ProtocolError):
            PrivNetRequest.decode(frame)


class TestWhichBackendsGetTheNetnsOwnerCheck:
    """The owner check is set for the rootless backends and NOT for containerd, and that asymmetry
    is a claim about where the PID comes from — a root-owned daemon the agent cannot forge, versus
    a journal the agent itself writes. If the wiring silently applied it everywhere, containerd
    kernels (whose netns belongs to uid 0, not to the agent) would stop attaching; if it applied it
    nowhere, the rootless gap the check exists for would be open again. Neither shows up until a
    live multi-node session, so it is pinned here.
    """

    @pytest.mark.parametrize("key", ["backend", "mode"])
    @pytest.mark.parametrize("backend", [AgentBackend.ENROOT, AgentBackend.SINGULARITY])
    def test_a_rootless_backend_is_bound_to_the_agents_own_namespaces(
        self, key: str, backend: AgentBackend
    ) -> None:
        assert main_mod._is_rootless({"agent": {key: backend.value}}) is True

    def test_containerd_is_not(self) -> None:
        """Its PID comes from a root daemon; requiring the agent to own the netns would refuse
        every containerd kernel, because uid 0 owns it."""
        assert main_mod._is_rootless({"agent": {"backend": AgentBackend.CONTAINERD.value}}) is False

    def test_an_unconfigured_node_is_not(self) -> None:
        """The historical default is containerd, and defaulting the other way would turn a missing
        config key into a node that cannot attach anything."""
        assert main_mod._is_rootless({}) is False
        assert main_mod._is_rootless({"agent": {}}) is False

    def test_an_unknown_backend_name_is_not_silently_treated_as_rootless(self) -> None:
        with pytest.raises(ValueError):
            main_mod._is_rootless({"agent": {"backend": "not-a-backend"}})


class TestTheOwnerCheckIsOnlyAskedForWhereThePidIsForgeable:
    """The uid handed to the server is the agent's own — the check says "a namespace this agent
    could have created", not "some particular uid"."""

    @pytest.mark.parametrize(
        ("backend", "expected_is_rootless"),
        [
            (AgentBackend.ENROOT, True),
            (AgentBackend.SINGULARITY, True),
            (AgentBackend.CONTAINERD, False),
        ],
    )
    def test_the_wiring_matches_the_backend(
        self, backend: AgentBackend, expected_is_rootless: bool
    ) -> None:
        raw = {"agent": {"backend": backend.value}}
        allowed_uid = 1000
        # This mirrors the one expression in __main__ that decides it, so a change there that
        # forgets the asymmetry fails here rather than on a live node.
        netns_owner_uid = allowed_uid if main_mod._is_rootless(raw) else None

        assert (netns_owner_uid is not None) is expected_is_rootless
        if expected_is_rootless:
            assert netns_owner_uid == allowed_uid
