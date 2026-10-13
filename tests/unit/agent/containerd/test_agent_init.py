from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig, ContainerdConfig
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.errors.agent import InvalidAgentConfigError
from ai.backend.agent.errors.containerd import RuntimeProfileLoadError
from ai.backend.common.types import KernelCreationConfig, SlotName

from .conftest import FakeProfile

LOAD_TARGET = "ai.backend.agent.containerd.agent.load_runtime_profiles"


@pytest.fixture
def base_init(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(AbstractAgent, "__init__", return_value=None)


def _local_config(
    containerd: dict[str, Any],
    init_timeout_sec: float = 7.5,
    *,
    bind_host: str = "",
    advertised_host: str | None = None,
) -> AgentUnifiedConfig:
    config = MagicMock()
    config.container.bind_host = bind_host
    config.container.advertised_host = advertised_host
    config.container.port_range = (30000, 31000)
    config.containerd = ContainerdConfig.model_validate(containerd)
    config.kernel_lifecycles.init_timeout_sec = init_timeout_sec
    return cast(AgentUnifiedConfig, config)


def _new_agent(local_config: AgentUnifiedConfig) -> ContainerdAgent:
    agent = object.__new__(ContainerdAgent)
    ContainerdAgent.__init__(agent, MagicMock(), local_config, computers={}, slots={})
    return agent


class TestContainerdAgentInit:
    def test_profiles_are_loaded_from_the_config(
        self, mocker: MockerFixture, base_init: MagicMock
    ) -> None:
        profiles = [FakeProfile("coco-tdx", accepts=True)]
        load = mocker.patch(LOAD_TARGET, return_value=profiles)
        config = _local_config({
            "runtime-profiles": ["coco-tdx"],
            "profiles": {"coco-tdx": {"standin-image": "ref"}},
        })

        agent = _new_agent(config)

        load.assert_called_once_with(["coco-tdx"], {"coco-tdx": {"standin-image": "ref"}})
        assert agent._runtime_profiles == profiles

    def test_required_slots_become_a_frozenset_of_slot_names(
        self, mocker: MockerFixture, base_init: MagicMock
    ) -> None:
        mocker.patch(LOAD_TARGET, return_value=[])
        config = _local_config({"profile-required-slots": ["confidential.tdx", "confidential.tdx"]})

        agent = _new_agent(config)

        assert agent._profile_required_slots == frozenset({SlotName("confidential.tdx")})

    def test_runc_readiness_timeout_follows_init_timeout(
        self,
        mocker: MockerFixture,
        base_init: MagicMock,
        kernel_config: KernelCreationConfig,
    ) -> None:
        mocker.patch(LOAD_TARGET, return_value=[])

        agent = _new_agent(_local_config({}, init_timeout_sec=7.5))

        launch = MagicMock(config=kernel_config)
        assert agent._runc_profile.plan(launch).readiness.timeout_s == 7.5

    def test_base_init_receives_the_remaining_arguments(
        self, mocker: MockerFixture, base_init: MagicMock
    ) -> None:
        mocker.patch(LOAD_TARGET, return_value=[])
        config = _local_config({})

        _new_agent(config)

        _, kwargs = base_init.call_args
        assert kwargs == {"computers": {}, "slots": {}}

    def test_load_error_stops_the_agent_before_the_base_init(
        self, mocker: MockerFixture, base_init: MagicMock
    ) -> None:
        mocker.patch(LOAD_TARGET, side_effect=RuntimeProfileLoadError("not installed"))

        with pytest.raises(RuntimeProfileLoadError, match="not installed"):
            _new_agent(_local_config({"runtime-profiles": ["coco-tdx"]}))

        base_init.assert_not_called()

    def test_network_follows_the_bridge_config(
        self, mocker: MockerFixture, base_init: MagicMock
    ) -> None:
        mocker.patch(LOAD_TARGET, return_value=[])
        config = _local_config({"bridge-name": "bai-x", "bridge-subnet": "172.30.5.0/24"})

        agent = _new_agent(config)

        assert agent._network._bridge == "bai-x"
        assert str(agent._network._gateway) == "172.30.5.1"

    @pytest.mark.parametrize(
        ("bind_host", "advertised_host"),
        [
            ("127.0.0.1", None),
            ("127.1.2.3", None),
            ("localhost", None),
            ("node.example.com", None),
            ("::1", None),
            ("fe80::1", None),
            ("", "127.0.0.1"),
            ("", "localhost"),
            ("", "LocalHost"),
            ("", "::1"),
            ("10.0.0.5", "127.1.2.3"),
        ],
    )
    def test_loopback_and_non_ipv4_hosts_are_refused_before_the_base_init(
        self,
        mocker: MockerFixture,
        base_init: MagicMock,
        bind_host: str,
        advertised_host: str | None,
    ) -> None:
        mocker.patch(LOAD_TARGET, return_value=[])
        config = _local_config({}, bind_host=bind_host, advertised_host=advertised_host)

        with pytest.raises(InvalidAgentConfigError, match=r"container\.(bind|advertised)-host"):
            _new_agent(config)

        base_init.assert_not_called()

    @pytest.mark.parametrize(
        ("bind_host", "advertised_host"),
        [("", None), ("0.0.0.0", "node.example.com"), ("10.0.0.5", "10.0.0.6")],
    )
    def test_other_hosts_are_accepted(
        self,
        mocker: MockerFixture,
        base_init: MagicMock,
        bind_host: str,
        advertised_host: str | None,
    ) -> None:
        mocker.patch(LOAD_TARGET, return_value=[])

        _new_agent(_local_config({}, bind_host=bind_host, advertised_host=advertised_host))
