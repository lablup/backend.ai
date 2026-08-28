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
