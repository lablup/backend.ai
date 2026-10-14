"""Where the agent calls its container-network plugins: STATUS before each heartbeat, GC at the
start-up scan, DEL when a kernel is cleaned."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

import ai.backend.agent.agent as agent_mod
from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.network.cni import CNI_ARG_KERNEL_ID, CNI_ARG_SESSION_ID, CniStatus
from ai.backend.common.docker import LabelName
from ai.backend.common.types import KernelId


def _with_plugins(**plugins: Any) -> Any:
    return SimpleNamespace(cni_plugin_ctx=SimpleNamespace(plugins=plugins))


class TestAPluginThatCannotServe:
    async def test_its_reason_keeps_the_node_out(self) -> None:
        plugin = SimpleNamespace(
            status=AsyncMock(return_value=CniStatus(not_ready_reason="the helper is gone"))
        )
        reason = await AbstractAgent.not_serving_reason(_with_plugins(example=plugin))
        assert reason is not None and "example" in reason and "the helper is gone" in reason

    async def test_a_plugin_that_does_not_answer_is_a_reason_too(self) -> None:
        plugin = SimpleNamespace(status=AsyncMock(side_effect=RuntimeError("socket closed")))
        reason = await AbstractAgent.not_serving_reason(_with_plugins(example=plugin))
        assert reason is not None and "socket closed" in reason

    async def test_a_plugin_that_hangs_is_a_reason_and_does_not_hold_the_heartbeat(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(agent_mod, "CNI_STATUS_TIMEOUT", 0.01)

        async def never_answers() -> CniStatus:
            await asyncio.Event().wait()
            raise AssertionError("unreachable")

        plugin = SimpleNamespace(status=never_answers)
        reason = await AbstractAgent.not_serving_reason(_with_plugins(example=plugin))
        assert reason is not None and "did not answer" in reason

    async def test_a_ready_plugin_gives_no_reason(self) -> None:
        plugin = SimpleNamespace(status=AsyncMock(return_value=CniStatus()))
        assert await AbstractAgent.not_serving_reason(_with_plugins(example=plugin)) is None


class TestTheHeartbeatIsTheClaimToTakeWork:
    """The manager marks a node ALIVE on a heartbeat alone, so it is withheld while a plugin
    cannot serve, and the manager is told once."""

    @staticmethod
    def _agent(reasons: list[str | None]) -> Any:
        """The slice of the agent `heartbeat` touches, answering `not_serving_reason` from
        ``reasons`` one tick at a time."""
        answers = iter(reasons)

        async def not_serving_reason() -> str | None:
            return next(answers)

        return SimpleNamespace(
            _announcing=True,
            not_serving_reason=not_serving_reason,
            computers={},
            slots={},
            rpc_addr=SimpleNamespace(host="10.0.0.1", port=6011),
            local_config=SimpleNamespace(
                agent=SimpleNamespace(
                    region=None,
                    initial_resource_group_name="default",
                    force_terminate_abusing_containers=False,
                ),
            ),
            agent_public_key=None,
            _get_public_host=lambda: "10.0.0.1",
            images={},
            id="i-abc123",
            anycast_event=AsyncMock(),
            valkey_image_client=SimpleNamespace(add_agent_installed_images=AsyncMock()),
        )

    @staticmethod
    def _events(agent: Any) -> list[str]:
        return [type(call.args[0]).__name__ for call in agent.anycast_event.await_args_list]

    async def test_a_node_that_cannot_take_work_stops_heartbeating(self) -> None:
        agent = self._agent(["the helper is gone", "the helper is gone"])
        await AbstractAgent.heartbeat(agent)
        await AbstractAgent.heartbeat(agent)
        assert self._events(agent) == ["AgentTerminatedEvent"]
        assert agent.anycast_event.await_args_list[0].args[0].reason == "agent-restart"

    async def test_the_first_heartbeat_after_recovery_announces_the_node_again(self) -> None:
        agent = self._agent(["the helper is gone", None])
        await AbstractAgent.heartbeat(agent)
        await AbstractAgent.heartbeat(agent)
        assert self._events(agent) == ["AgentTerminatedEvent", "AgentHeartbeatEvent"]
        assert agent._announcing is True

    async def test_a_restarting_event_that_was_not_sent_is_sent_on_the_next_tick(self) -> None:
        agent = self._agent(["the helper is gone", "the helper is gone"])
        agent.anycast_event.side_effect = [ConnectionError("redis is down"), None]
        await AbstractAgent.heartbeat(agent)
        assert agent._announcing is True
        await AbstractAgent.heartbeat(agent)
        assert self._events(agent) == ["AgentTerminatedEvent", "AgentTerminatedEvent"]
        assert agent._announcing is False

    async def test_a_node_that_can_take_work_just_heartbeats(self) -> None:
        agent = self._agent([None, None])
        await AbstractAgent.heartbeat(agent)
        await AbstractAgent.heartbeat(agent)
        assert self._events(agent) == ["AgentHeartbeatEvent", "AgentHeartbeatEvent"]


class TestTheStartUpGc:
    @staticmethod
    def _agent(containers: list[tuple[KernelId, Any]], **plugins: Any) -> Any:
        agent = _with_plugins(**plugins)
        agent.enumerate_containers = AsyncMock(return_value=containers)
        return agent

    async def test_each_plugin_is_told_the_containers_that_still_exist(self) -> None:
        kernel_id = KernelId(uuid4())
        session_id = str(uuid4())
        kernel = SimpleNamespace(id="cid-1", labels={LabelName.SESSION_ID: session_id})
        stray = SimpleNamespace(id="cid-2", labels={})
        plugin = SimpleNamespace(gc=AsyncMock())

        await AbstractAgent._gc_container_networks(
            self._agent([(kernel_id, kernel), (KernelId(uuid4()), stray)], example=plugin)
        )

        ((valid,), _) = plugin.gc.await_args
        assert [(a.container_id, dict(a.args)) for a in valid] == [
            ("cid-1", {CNI_ARG_SESSION_ID: session_id, CNI_ARG_KERNEL_ID: str(kernel_id)})
        ]

    async def test_a_failing_plugin_does_not_stop_the_rest(self) -> None:
        failing = SimpleNamespace(gc=AsyncMock(side_effect=RuntimeError("helper gone")))
        working = SimpleNamespace(gc=AsyncMock())

        await AbstractAgent._gc_container_networks(self._agent([], a=failing, b=working))

        working.gc.assert_awaited_once_with([])


class TestCleaningAKernelDetachesItsNetwork:
    async def test_every_plugin_gets_the_delete(self) -> None:
        first, second = SimpleNamespace(delete=AsyncMock()), SimpleNamespace(delete=AsyncMock())
        kernel_id = KernelId(uuid4())
        session_id = uuid4()
        agent = _with_plugins(a=first, b=second)
        agent.kernel_registry = {kernel_id: SimpleNamespace(session_id=session_id)}

        await DockerAgent._delete_container_network(cast(Any, agent), kernel_id, "cid-1")

        for plugin in (first, second):
            ((request,), _) = plugin.delete.await_args
            assert request.container_id == "cid-1"
            assert request.args == {
                CNI_ARG_KERNEL_ID: str(kernel_id),
                CNI_ARG_SESSION_ID: str(session_id),
            }

    async def test_a_failing_plugin_does_not_stop_the_rest(self) -> None:
        failing = SimpleNamespace(delete=AsyncMock(side_effect=RuntimeError("helper gone")))
        working = SimpleNamespace(delete=AsyncMock())
        agent = _with_plugins(a=failing, b=working)
        agent.kernel_registry = {}

        await DockerAgent._delete_container_network(cast(Any, agent), KernelId(uuid4()), "cid-1")

        working.delete.assert_awaited_once()


class TestTheNameserversAPluginIsGiven:
    async def test_the_configured_ones_win(self) -> None:
        agent = SimpleNamespace(
            local_config=SimpleNamespace(container=SimpleNamespace(dns=["10.0.0.53"]))
        )
        assert await AbstractAgent._container_nameservers(cast(Any, agent)) == ["10.0.0.53"]
