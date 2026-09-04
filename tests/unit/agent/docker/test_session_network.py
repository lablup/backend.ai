"""Which sessions the Docker backend takes over the networking of.

Getting this wrong is quiet in both directions. Claiming a session BAI does not build leaves the
container on ``NetworkMode: none`` with nothing ever attached — a kernel that starts and reaches
nothing. Declining one BAI does build hands it to Docker's own networking while the agent also
moves a device in, putting it on two networks of which one is routed by nobody.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from ai.backend.agent.docker.session_network import (
    NO_NETWORK_MODE,
    is_session_networked,
    make_docker_locator,
)
from ai.backend.agent.network.locator import ContainerLocator


def _info(network_config: dict[str, Any] | None) -> Any:
    return cast(Any, {"network_config": network_config})


class TestWhoseNetworkItIs:
    def test_a_bep1062_backend_is_ours(self) -> None:
        assert is_session_networked(
            _info({"backend": "vxlan", "subnet": "10.128.5.0/24", "vni": 4097, "mtu": 1450})
        )

    def test_a_node_local_bridge_is_ours_too(self) -> None:
        # Single-node sessions carry a synthesized bridge config; the same attach path applies.
        assert is_session_networked(_info({"backend": "bridge", "subnet": "172.30.0.0/26"}))

    def test_swarm_overlay_is_dockers(self) -> None:
        # 'overlay' under `mode` is Docker Swarm — Docker's control plane, not ours to intercept.
        assert not is_session_networked(_info({"mode": "overlay", "network_name": "bai-net"}))

    def test_a_v1_bridge_driver_is_dockers(self) -> None:
        assert not is_session_networked(_info({"mode": "bridge", "network_name": "bai-net"}))

    def test_no_cluster_network_is_not_ours(self) -> None:
        assert not is_session_networked(_info({}))

    def test_a_missing_network_config_is_not_ours(self) -> None:
        # Single-container sessions arrive with nothing here at all.
        assert not is_session_networked(_info(None))

    def test_mode_alongside_a_backend_does_not_win(self) -> None:
        # The manager may carry both; `backend` names the data plane and is what decides.
        assert is_session_networked(_info({"mode": "bridge", "backend": "vxlan"}))


class TestTheLocator:
    def test_docker_brings_a_locator(self) -> None:
        # And no runtime: the session network's two-collaborator split is what makes that legal.
        assert isinstance(make_docker_locator(), ContainerLocator)

    def test_it_declines_to_place_cgroups(self) -> None:
        # Docker places its own; only the rootless backends ask the privnet to create one.
        with pytest.raises(NotImplementedError):
            make_docker_locator().cgroup_path("c1")


def test_the_no_network_mode_is_dockers_own_word() -> None:
    # Not a BAI constant Docker would ignore: this is the value the daemon understands.
    assert NO_NETWORK_MODE == "none"
