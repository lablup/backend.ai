"""When a Docker agent announces itself and advertises its overlay identity (BEP-1079).

What the advert contains is pinned in tests/unit/agent/network/test_identity.py; these pin when
the Docker agent publishes it, and what it answers when asked whether it can take work.
"""

from __future__ import annotations

import asyncio
import inspect
import pathlib
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import ai.backend.agent.server as agent_server
from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.docker.agent import DockerAgent, DockerKernelCreationContext
from ai.backend.agent.errors import AgentInitializationError
from ai.backend.agent.errors.agent import ContainerCreationError


class TestTheNodeIsAnnouncedOnlyOnceItCanServe:
    """A11c. Two things announce this node: the started event, and the heartbeat -- the manager
    marks an agent ALIVE on a heartbeat alone. Both used to begin inside `__ainit__`, while the
    backend still had work to do (the socket relay, the network plugin context, the advert that
    admits it to a cluster-network session) and before there was an RPC server to take the work
    that would follow."""

    def test_the_base_agent_neither_announces_nor_heartbeats_from_ainit(self) -> None:
        source = (
            pathlib.Path(inspect.getfile(AbstractAgent)).read_text().split("async def __ainit__")[1]
        )
        body = source.split("\n    async def ")[0]
        assert "AgentStartedEvent" not in body, (
            "the node is announced while its backend is still starting"
        )
        assert "_local_cron.start()" not in body, (
            "the heartbeat starts while its backend is still starting, and a heartbeat alone"
            " marks the node ALIVE"
        )

    def test_start_serving_does_both(self) -> None:
        source = inspect.getsource(AbstractAgent.start_serving)
        assert "_local_cron.start()" in source
        assert "AgentStartedEvent" in source

    def _heartbeating_agent(self, reasons: list[str | None]) -> Any:
        """The slice of the agent `heartbeat` touches, answering `not_serving_reason` from
        ``reasons`` one tick at a time."""
        stub = SimpleNamespace(
            _announcing=True,
            computers={},
            slots={},
            rpc_addr=SimpleNamespace(host="10.0.0.1", port=6011),
            local_config=SimpleNamespace(
                agent=SimpleNamespace(
                    region=None,
                    initial_resource_group_name="default",
                    force_terminate_abusing_containers=False,
                ),
                debug=SimpleNamespace(log_heartbeats=False),
            ),
            agent_public_key=None,
            _get_public_host=lambda: "10.0.0.1",
            images={},
            id="i-abc123",
            anycast_event=AsyncMock(),
            valkey_image_client=SimpleNamespace(add_agent_installed_images=AsyncMock()),
        )
        answers = iter(reasons)

        async def not_serving_reason() -> str | None:
            return next(answers)

        stub.not_serving_reason = not_serving_reason
        return stub

    @staticmethod
    def _events(stub: Any) -> list[str]:
        return [type(call.args[0]).__name__ for call in stub.anycast_event.await_args_list]

    async def test_a_node_that_cannot_take_work_stops_heartbeating(self) -> None:
        """The heartbeat IS the claim that this node can take work -- the manager marks it ALIVE
        on that alone -- so it is withheld while the claim is false, and the manager is told at
        once rather than finding the node lost forty seconds later."""
        stub = self._heartbeating_agent(["the helper is gone", "the helper is gone"])
        await AbstractAgent.heartbeat(stub)
        await AbstractAgent.heartbeat(stub)
        assert self._events(stub) == ["AgentTerminatedEvent"], (
            "expected one restart announcement and no heartbeat"
        )
        assert stub.anycast_event.await_args_list[0].args[0].reason == "agent-restart"

    async def test_the_first_heartbeat_after_recovery_announces_the_node_again(self) -> None:
        stub = self._heartbeating_agent(["the helper is gone", None])
        await AbstractAgent.heartbeat(stub)
        await AbstractAgent.heartbeat(stub)
        assert self._events(stub) == ["AgentTerminatedEvent", "AgentHeartbeatEvent"]
        assert stub._announcing is True

    async def test_a_node_that_can_take_work_just_heartbeats(self) -> None:
        stub = self._heartbeating_agent([None, None])
        await AbstractAgent.heartbeat(stub)
        await AbstractAgent.heartbeat(stub)
        assert self._events(stub) == ["AgentHeartbeatEvent", "AgentHeartbeatEvent"]

    async def test_the_docker_agent_answers_with_its_privnet(self, tmp_path: pathlib.Path) -> None:
        """On a privnet-backed node every session's devices are made by that process, the
        single-node bridge included, so a node that cannot reach it can serve nothing."""
        stub = SimpleNamespace(_privnet_socket=str(tmp_path / "absent.sock"))
        reason = await DockerAgent.not_serving_reason(cast(Any, stub))
        assert reason is not None and "does not exist" in reason

    async def test_a_node_without_a_privnet_has_nothing_to_answer_for(self) -> None:
        stub = SimpleNamespace(_privnet_socket=None)
        assert await DockerAgent.not_serving_reason(cast(Any, stub)) is None

    async def test_a_swarm_cluster_does_not_publish_the_advert(self) -> None:
        """Under the Swarm driver nothing reads the BEP-1079 advert, so `start_serving` announces
        the node and stops there -- no publish, no refresh task."""
        agent = object.__new__(DockerAgent)
        agent._cluster_network_owned = False
        agent._network_identity = MagicMock(start=AsyncMock())
        with patch.object(AbstractAgent, "start_serving", AsyncMock()):
            await agent.start_serving()
        agent._network_identity.start.assert_not_awaited()

    async def test_announcing_before_the_transport_serves_is_refused(self) -> None:
        """Refuse announcements before the transport enters serving state."""
        server = object.__new__(agent_server.AgentRPCServer)
        server._transport_entered = False
        server.runtime = MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock())

        with pytest.raises(AgentInitializationError, match="before its RPC transport is serving"):
            await server.start_serving()

        server.runtime.start_serving.assert_not_awaited()

    async def test_it_announces_once_the_transport_is_serving(self) -> None:
        server = object.__new__(agent_server.AgentRPCServer)
        server._transport_entered = False
        server.runtime = MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock())
        server.rpc_server = MagicMock(__aenter__=AsyncMock())

        await server.__aenter__()
        await server.start_serving()

        server.runtime.start_serving.assert_awaited_once()

    async def test_stopping_takes_the_announcement_back(self) -> None:
        # `aobject.new` does not call cleanup when `__ainit__` raises, and a failure after the
        # transport is entered unwinds without it either.
        server = object.__new__(agent_server.AgentRPCServer)
        server._transport_entered = True
        server.runtime = MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock())

        await server.stop_serving()

        server.runtime.stop_serving.assert_awaited_once()
        with pytest.raises(AgentInitializationError):
            await server.start_serving()


class TestAContainerThatIsUpWhenSomethingFails:
    """A11g. The container is created and started, and only then is the session network attached.
    Everything from creation onwards has to carry the container's id out with it: a plain
    exception reached the agent's handler as "kernel failed" with no id, `destroy_kernel` had
    nothing to act on, and the container went on running with its kernel already gone from the
    registry."""

    def _context(self) -> Any:
        ctx = object.__new__(DockerKernelCreationContext)
        ctx._session_networked = True
        ctx.internal_data = {}
        ctx.computers = {}
        return ctx

    async def test_a_session_network_attach_failure_names_the_container(self) -> None:
        ctx = self._context()

        async def _refuses(container: Any, cid: str, cluster_info: Any) -> None:
            raise RuntimeError("the privnet refused this session")

        ctx._attach_session_network = _refuses

        with pytest.raises(RuntimeError, match="privnet refused"):
            await ctx._provision_started_container(
                MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock(allocations={})
            )

    async def test_an_additional_network_failure_names_the_container(self) -> None:
        ctx = self._context()
        ctx._session_networked = False

        async def _refuses(docker: Any, container: Any, names: Any) -> None:
            raise RuntimeError("that network does not exist")

        ctx._attach_additional_networks = _refuses

        with pytest.raises(RuntimeError, match="does not exist"):
            await ctx._provision_started_container(
                MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock(allocations={})
            )

    async def test_the_caller_turns_those_into_a_named_container_failure(self) -> None:
        """The wrapper is what carries the id out, so the handler that destroys the kernel has
        something to destroy. Driven rather than read: the value of this is that a failure
        ARRIVES named, not that the source says so."""
        ctx = self._context()

        async def _refuses(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("the privnet refused this session")

        ctx._provision_started_container = _refuses
        caught: ContainerCreationError | None = None
        try:
            await DockerKernelCreationContext._provision_or_name_the_container(
                cast(Any, ctx), MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock()
            )
        except ContainerCreationError as e:
            caught = e

        assert caught is not None
        assert caught.container_id == "cid-1"


class TestACreateThatWasCancelled:
    """A11i. Cancellation is the ordinary way a create fails -- the launcher's timeout does it,
    and so does an agent shutdown -- and it is not an `Exception`, so no handler catching that
    reached it. A cancelled attach left the container running with its kernel already out of the
    registry and nothing queued to destroy it. And once a container exists the create's own undo
    must keep its hands off: the lifecycle stops the container, detaches it and removes its
    scratch, in that order, and deleting the scratch from here cuts across that."""

    def _agent(self, container_id: str | None) -> Any:
        """Enough of an agent to drive the unwind, and nothing else.

        `create_kernel` cannot be called without the whole agent, and the abstract base cannot be
        instantiated -- but the branch that decides what a failed create takes back is the whole
        of what is being tested, and an unbound call reaches it.
        """
        registry: dict[str, Any] = {}
        if container_id is not None:
            registry["k1"] = SimpleNamespace(container_id=container_id)
        return SimpleNamespace(
            kernel_registry=registry,
            inject_container_lifecycle_event=AsyncMock(),
            reconstruct_resource_usage=AsyncMock(),
        )

    async def test_a_container_that_exists_is_destroyed_and_nothing_else_is_touched(self) -> None:
        """The ownership boundary is container CREATION. A container that exists may be running --
        `docker start` can be cancelled after the daemon has acted on it -- and a running
        container holds its devices, its published ports and its scratch. All three go back
        through its teardown, which stops it first."""
        agent = self._agent("cid-1")
        undone = False

        async def _undo() -> None:
            nonlocal undone
            undone = True

        await AbstractAgent._unwind_failed_create(
            cast(Any, agent), cast(Any, "k1"), cast(Any, "s1"), [_undo]
        )

        agent.inject_container_lifecycle_event.assert_awaited_once()
        assert agent.inject_container_lifecycle_event.await_args.kwargs["container_id"] == "cid-1"
        assert not undone, "the scratch of a running container was deleted from under it"
        (
            agent.reconstruct_resource_usage.assert_not_awaited(),
            ("the allocation maps were rebuilt while a container was still holding its devices"),
        )

    async def test_with_no_container_the_undo_stack_runs(self) -> None:
        agent = self._agent(None)
        undone: list[str] = []

        async def _undo_scratch() -> None:
            undone.append("scratch")

        await AbstractAgent._unwind_failed_create(
            cast(Any, agent), cast(Any, "k1"), cast(Any, "s1"), [_undo_scratch]
        )

        assert undone == ["scratch"]
        agent.inject_container_lifecycle_event.assert_not_awaited()
        # The net under a failure that happened before the backend's own rollback could run.
        agent.reconstruct_resource_usage.assert_awaited_once()

    async def test_the_cleanup_survives_the_cancellation_that_triggered_it(self) -> None:
        # What is being unwound here is usually a cancellation, and a cleanup cancelled halfway
        # is the leak it exists to prevent.
        agent = self._agent("cid-1")
        started = asyncio.Event()

        async def _slow_destroy(*args: Any, **kwargs: Any) -> None:
            started.set()
            await asyncio.sleep(0.05)
            agent.destroyed = True

        agent.inject_container_lifecycle_event = _slow_destroy
        task = asyncio.create_task(
            AbstractAgent._unwind_failed_create(
                cast(Any, agent), cast(Any, "k1"), cast(Any, "s1"), []
            )
        )
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.1)

        assert getattr(agent, "destroyed", False), "the teardown was cancelled halfway"

    async def test_an_undo_that_raises_does_not_stop_the_rest(self) -> None:
        agent = self._agent(None)
        undone: list[str] = []

        async def _boom() -> None:
            raise RuntimeError("could not remove it")

        async def _works() -> None:
            undone.append("worked")

        await AbstractAgent._unwind_failed_create(
            cast(Any, agent), cast(Any, "k1"), cast(Any, "s1"), [_works, _boom]
        )

        assert undone == ["worked"]
        agent.reconstruct_resource_usage.assert_awaited_once()
