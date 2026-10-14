"""How a failed or cancelled create gives back what it made on the host."""

from __future__ import annotations

import asyncio
import functools
import json
import pickle
import uuid
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.docker.agent import DockerKernelCreationContext
from ai.backend.agent.errors.agent import ContainerCreationError, ContainerCreationFailedError
from ai.backend.agent.errors.resources import PortPoolExhaustedError
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.types import ContainerLifecycleEvent, KernelLifecycleStatus, LifecycleEvent
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    DeviceName,
    KernelId,
    SessionId,
    SessionTypes,
    SlotName,
)


class TestAContainerThatIsUpWhenSomethingFails:
    """Every failure after container creation carries the container id out."""

    def _context(self) -> Any:
        ctx = object.__new__(DockerKernelCreationContext)
        ctx.internal_data = {}
        ctx.computers = {}
        return ctx

    async def test_the_caller_turns_those_into_a_named_container_failure(self) -> None:
        ctx = self._context()

        async def _refuses(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("an additional network refused this container")

        ctx._provision_started_container = _refuses
        with pytest.raises(ContainerCreationError) as caught:
            await DockerKernelCreationContext._provision_or_name_the_container(
                cast(Any, ctx), MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock()
            )

        assert caught.value.container_id == "cid-1"

    async def test_a_named_failure_passes_through_unchanged(self) -> None:
        ctx = self._context()
        original = ContainerCreationError(container_id="cid-1", message="sudoers failed")

        async def _refuses(*args: Any, **kwargs: Any) -> None:
            raise original

        ctx._provision_started_container = _refuses
        with pytest.raises(ContainerCreationError) as caught:
            await DockerKernelCreationContext._provision_or_name_the_container(
                cast(Any, ctx), MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock()
            )

        assert caught.value is original


class _Kernel(dict[str, Any]):
    """A kernel object as the registry and the lifecycle handlers see it."""

    def __init__(self, container_id: str | None = None) -> None:
        super().__init__(container_id=container_id)
        self.termination_reason: KernelLifecycleEventReason | None = None
        self.state = KernelLifecycleStatus.PREPARING
        self.runner = None
        self.clean_event = None
        self.close = AsyncMock()

    @property
    def container_id(self) -> str | None:
        return cast(str | None, self["container_id"])


def _agent(registry: dict[Any, Any] | None = None) -> Any:
    agent = SimpleNamespace(
        kernel_registry=registry if registry is not None else {},
        restarting_kernels={},
        inject_container_lifecycle_event=AsyncMock(),
        reconstruct_resource_usage=AsyncMock(),
    )
    agent._take_back_failed_create = functools.partial(
        AbstractAgent._take_back_failed_create, cast(Any, agent)
    )
    return agent


async def _unwind(
    agent: Any, registered: Any, made: list[Any], kernel_id: Any = "k1", session_id: Any = "s1"
) -> None:
    await AbstractAgent._unwind_failed_create(agent, kernel_id, session_id, registered, made)


class TestAFailedCreateThatRegisteredAKernel:
    """The kernel this create registered gets exactly one DESTROY; its CLEAN does the rest."""

    async def test_a_kernel_with_a_container_gets_one_destroy_naming_it(self) -> None:
        kernel = _Kernel("cid-1")
        agent = _agent({"k1": kernel})
        undone: list[str] = []

        async def _undo() -> None:
            undone.append("scratch")

        await _unwind(agent, kernel, [_undo])

        agent.inject_container_lifecycle_event.assert_awaited_once()
        call = agent.inject_container_lifecycle_event.await_args
        assert call.args[2] == LifecycleEvent.DESTROY
        assert call.args[3] == KernelLifecycleEventReason.FAILED_TO_CREATE
        assert call.kwargs["container_id"] == "cid-1"
        assert undone == [], "the scratch of a running container was deleted from under it"
        agent.reconstruct_resource_usage.assert_not_awaited()

    async def test_a_kernel_with_no_container_gets_one_destroy_without_one(self) -> None:
        kernel = _Kernel(None)
        agent = _agent({"k1": kernel})
        undone: list[str] = []

        async def _undo() -> None:
            undone.append("scratch")

        await _unwind(agent, kernel, [_undo])

        agent.inject_container_lifecycle_event.assert_awaited_once()
        call = agent.inject_container_lifecycle_event.await_args
        assert call.args[2] == LifecycleEvent.DESTROY
        assert call.kwargs["container_id"] is None
        assert undone == [], "CLEAN cleans the scratch; the undo stack must not do it twice"

    async def test_the_destroy_carries_failed_to_start_when_the_start_failed(self) -> None:
        kernel = _Kernel("cid-1")
        kernel.termination_reason = KernelLifecycleEventReason.FAILED_TO_START
        agent = _agent({"k1": kernel})
        agent.container_lifecycle_queue = asyncio.Queue()
        agent.inject_container_lifecycle_event = functools.partial(
            AbstractAgent.inject_container_lifecycle_event, agent
        )

        await _unwind(agent, kernel, [])

        ev = agent.container_lifecycle_queue.get_nowait()
        assert ev.event == LifecycleEvent.DESTROY
        assert ev.reason == KernelLifecycleEventReason.FAILED_TO_START
        assert ev.container_id == "cid-1"
        assert agent.container_lifecycle_queue.empty()

    async def test_a_kernel_someone_else_already_destroyed_is_left_alone(self) -> None:
        agent = _agent({})

        await _unwind(agent, _Kernel("cid-1"), [])

        agent.inject_container_lifecycle_event.assert_not_awaited()

    async def test_a_failed_re_creation_is_forgotten_not_kept_for_a_restart(self) -> None:
        kernel = _Kernel(None)
        agent = _agent({"k1": kernel})
        agent.restarting_kernels["k1"] = MagicMock()

        await _unwind(agent, kernel, [])

        assert "k1" not in agent.restarting_kernels
        agent.inject_container_lifecycle_event.assert_awaited_once()

    async def test_a_kernel_already_being_destroyed_gets_no_second_destroy(self) -> None:
        kernel = _Kernel("cid-1")
        kernel.state = KernelLifecycleStatus.TERMINATING
        agent = _agent({"k1": kernel})
        agent.restarting_kernels["k1"] = MagicMock()

        await _unwind(agent, kernel, [])

        agent.inject_container_lifecycle_event.assert_not_awaited()
        assert "k1" not in agent.restarting_kernels, "that DESTROY's CLEAN would keep it"

    async def test_the_destroy_survives_the_cancellation_that_triggered_it(self) -> None:
        kernel = _Kernel("cid-1")
        agent = _agent({"k1": kernel})
        started = asyncio.Event()

        async def _slow_destroy(*args: Any, **kwargs: Any) -> None:
            started.set()
            await asyncio.sleep(0.05)
            agent.destroyed = True

        agent.inject_container_lifecycle_event = _slow_destroy
        task = asyncio.create_task(_unwind(agent, kernel, []))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.1)

        assert getattr(agent, "destroyed", False), "the teardown was cancelled halfway"


class TestAFailedCreateThatRegisteredNothing:
    """Before a kernel is registered, the undo stack runs; a restart's old kernel is untouched."""

    async def test_the_undo_stack_runs_in_reverse(self) -> None:
        agent = _agent()
        undone: list[str] = []

        async def _first() -> None:
            undone.append("first")

        async def _second() -> None:
            undone.append("second")

        await _unwind(agent, None, [_first, _second])

        assert undone == ["second", "first"]
        agent.inject_container_lifecycle_event.assert_not_awaited()
        agent.reconstruct_resource_usage.assert_awaited_once()

    async def test_an_undo_that_raises_does_not_stop_the_rest(self) -> None:
        agent = _agent()
        undone: list[str] = []

        async def _boom() -> None:
            raise RuntimeError("could not remove it")

        async def _works() -> None:
            undone.append("worked")

        await _unwind(agent, None, [_works, _boom])

        assert undone == ["worked"]
        agent.reconstruct_resource_usage.assert_awaited_once()

    async def test_a_second_cancel_cannot_skip_the_rest_of_the_undo_stack(self) -> None:
        agent = _agent()
        first_started = asyncio.Event()
        undone: list[str] = []

        async def _first() -> None:
            undone.append("first")

        async def _slow_second() -> None:
            first_started.set()
            await asyncio.sleep(0.05)
            undone.append("second")

        task = asyncio.create_task(_unwind(agent, None, [_first, _slow_second]))
        await first_started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.1)

        assert undone == ["second", "first"]
        agent.reconstruct_resource_usage.assert_awaited_once()


class TestTheCleanOfAKernelThatNeverStarted:
    """The DESTROY without a container ends in a CLEAN that forgets the kernel and frees its ports."""

    async def test_it_is_forgotten_its_ports_freed_and_reported(self) -> None:
        kernel_id, session_id = uuid.uuid4(), uuid.uuid4()
        kernel = _Kernel(None)
        kernel["host_ports"] = [30001, 30002]
        agent = SimpleNamespace(
            _ongoing_destruction_tasks={},
            stat_ctx=SimpleNamespace(remove_kernel_metric=AsyncMock()),
            registry_lock=asyncio.Lock(),
            kernel_registry={kernel_id: kernel},
            restarting_kernels={},
            clean_kernel=AsyncMock(),
            _restore_ports=MagicMock(),
            reconstruct_resource_usage=AsyncMock(),
            anycast_and_broadcast_event=AsyncMock(),
            produce_error_event=AsyncMock(),
        )
        ev = ContainerLifecycleEvent(
            KernelId(kernel_id),
            SessionId(session_id),
            None,
            LifecycleEvent.CLEAN,
            KernelLifecycleEventReason.FAILED_TO_CREATE,
        )

        await AbstractAgent._handle_clean_event(cast(Any, agent), ev)

        agent.clean_kernel.assert_awaited_once_with(kernel_id, None, False)
        assert kernel_id not in agent.kernel_registry
        agent._restore_ports.assert_called_once_with([30001, 30002])
        kernel.close.assert_awaited_once()
        anycast, broadcast = agent.anycast_and_broadcast_event.await_args.args
        assert anycast.reason == KernelLifecycleEventReason.FAILED_TO_CREATE
        assert broadcast.reason == KernelLifecycleEventReason.FAILED_TO_CREATE


class TestARestartWhoseReCreationFails:
    """The failure reaches the caller, the kernel is no longer tracked as restarting, and an
    old object nothing replaced is cleaned once more and forgotten."""

    def _agent(self, kernel_id: Any, registry: dict[Any, Any], create: Any) -> Any:
        agent = SimpleNamespace(
            restarting_kernels={},
            kernel_registry=registry,
            container_lifecycle_queue=asyncio.Queue(),
            create_kernel=create,
        )
        agent._forget_kernel_of_failed_restart = functools.partial(
            AbstractAgent._forget_kernel_of_failed_restart, cast(Any, agent)
        )

        async def _load_config(_kid: Any, name: str) -> bytes:
            return pickle.dumps({}) if name == "kconfig.dat" else json.dumps({}).encode()

        async def _destroy(*args: Any, **kwargs: Any) -> None:
            agent.restarting_kernels[kernel_id].destroy_event.set()

        agent.restart_kernel__load_config = _load_config
        agent.inject_container_lifecycle_event = _destroy
        return agent

    async def _restart(self, agent: Any, kernel_id: Any) -> None:
        ownership = SimpleNamespace(kernel_id=kernel_id, session_id=uuid.uuid4())
        await AbstractAgent.restart_kernel(
            cast(Any, agent), cast(Any, ownership), MagicMock(), cast(Any, {})
        )

    async def test_an_old_kernel_left_by_a_failure_before_registration_gets_a_clean(
        self,
    ) -> None:
        kernel_id = uuid.uuid4()
        old = _Kernel("old-cid")
        agent = self._agent(
            kernel_id, {kernel_id: old}, AsyncMock(side_effect=RuntimeError("no image"))
        )
        seen_restarting: list[bool] = []
        put = agent.container_lifecycle_queue.put

        async def _put(ev: ContainerLifecycleEvent) -> None:
            seen_restarting.append(ev.kernel_id in agent.restarting_kernels)
            await put(ev)

        agent.container_lifecycle_queue.put = _put

        with pytest.raises(RuntimeError):
            await self._restart(agent, kernel_id)

        ev = agent.container_lifecycle_queue.get_nowait()
        assert ev.event == LifecycleEvent.CLEAN
        assert ev.reason == KernelLifecycleEventReason.FAILED_TO_CREATE
        assert ev.container_id is None, "the old container is already deleted"
        assert seen_restarting == [False], "a CLEAN of a restarting kernel keeps it"
        assert agent.container_lifecycle_queue.empty()

    async def test_a_newly_registered_kernel_is_left_to_the_create_s_own_unwind(self) -> None:
        kernel_id = uuid.uuid4()
        old, new = _Kernel("old-cid"), _Kernel("new-cid")
        registry: dict[Any, Any] = {kernel_id: old}

        async def _registers_then_fails(*args: Any, **kwargs: Any) -> None:
            registry[kernel_id] = new
            raise RuntimeError("start failed")

        agent = self._agent(kernel_id, registry, _registers_then_fails)

        with pytest.raises(RuntimeError):
            await self._restart(agent, kernel_id)

        assert agent.container_lifecycle_queue.empty()

    async def test_the_clean_forgets_the_old_kernel_and_reports_it_once(self) -> None:
        kernel_id, session_id = uuid.uuid4(), uuid.uuid4()
        old = _Kernel("old-cid")
        old["host_ports"] = [30001]
        agent = SimpleNamespace(
            _ongoing_destruction_tasks={},
            stat_ctx=SimpleNamespace(remove_kernel_metric=AsyncMock()),
            registry_lock=asyncio.Lock(),
            kernel_registry={kernel_id: old},
            restarting_kernels={kernel_id: SimpleNamespace(destroy_event=asyncio.Event())},
            clean_kernel=AsyncMock(),
            _restore_ports=MagicMock(),
            reconstruct_resource_usage=AsyncMock(),
            anycast_and_broadcast_event=AsyncMock(),
            produce_error_event=AsyncMock(),
            container_lifecycle_queue=asyncio.Queue(),
        )
        restart_clean = ContainerLifecycleEvent(
            KernelId(kernel_id),
            SessionId(session_id),
            ContainerId("old-cid"),
            LifecycleEvent.CLEAN,
            KernelLifecycleEventReason.RESTARTING,
        )
        await AbstractAgent._handle_clean_event(cast(Any, agent), restart_clean)
        agent._restore_ports.assert_called_once_with([30001])
        agent.restarting_kernels.clear()

        await AbstractAgent._forget_kernel_of_failed_restart(
            cast(Any, agent), KernelId(kernel_id), SessionId(session_id), cast(Any, old)
        )
        await AbstractAgent._handle_clean_event(
            cast(Any, agent), agent.container_lifecycle_queue.get_nowait()
        )

        assert kernel_id not in agent.kernel_registry
        agent.clean_kernel.assert_awaited_with(kernel_id, None, False)
        assert agent._restore_ports.call_count == 1, "ports another kernel may hold were freed"
        agent.reconstruct_resource_usage.assert_awaited_once()
        agent.anycast_and_broadcast_event.assert_awaited_once()
        anycast, _ = agent.anycast_and_broadcast_event.await_args.args
        assert anycast.reason == KernelLifecycleEventReason.FAILED_TO_CREATE

    async def test_it_raises_and_stops_tracking_the_restart(self) -> None:
        kernel_id = uuid.uuid4()
        agent = self._agent(
            kernel_id, {}, AsyncMock(side_effect=ContainerCreationError("cid", "boom"))
        )

        with pytest.raises(ContainerCreationError):
            await self._restart(agent, kernel_id)

        assert kernel_id not in agent.restarting_kernels


class _StartKernel(dict[str, Any]):
    def __init__(self) -> None:
        super().__init__()
        self.resource_spec = SimpleNamespace(allocations={})
        self.service_ports: list[Any] = []
        self.environ: dict[str, str] = {}

    def set_container_id(self, cid: str) -> None:
        self["container_id"] = cid


class TestThePortsAStartTakes:
    """Ports are on the kernel from the moment they are taken, and only CLEAN gives them back."""

    def _context(self, tmp_path: Path, pool: PortPool) -> Any:
        ctx = object.__new__(DockerKernelCreationContext)
        ctx.kernel_config = cast(Any, {"image": {"labels": {}}, "cluster_hostname": "main1"})
        ctx.local_config = MagicMock()
        ctx.local_config.debug.log_kernel_config = False
        ctx.port_pool = pool
        ctx.cluster_ssh_port_mapping = None
        ctx.network_plugin_ctx = MagicMock()
        ctx.image_ref = MagicMock()
        ctx.ownership_data = MagicMock()
        ctx.internal_data = {}
        ctx.container_configs = []
        ctx.computer_docker_args = {"HostConfig": {}}
        ctx.computers = {}
        ctx.resource_lock = asyncio.Lock()
        ctx.domain_socket_proxies = []
        ctx.config_dir = tmp_path
        ctx.agent_id = AgentId("a1")
        ctx.kernel_id = KernelId(uuid.uuid4())
        ctx.session_id = SessionId(uuid.uuid4())
        return ctx

    @pytest.fixture
    def pool(self) -> PortPool:
        return PortPool((30000, 30009), cooldown_sec=0)

    @pytest.fixture
    def docker(self) -> Iterator[MagicMock]:
        docker = MagicMock()
        docker.close = AsyncMock()
        with (
            patch("ai.backend.agent.docker.agent.Docker", return_value=docker),
            patch("ai.backend.agent.docker.agent._build_log_config"),
        ):
            yield docker

    async def _start(self, ctx: Any, kernel: _StartKernel, mode: str = "bridge") -> None:
        await DockerKernelCreationContext.start_container(
            ctx, cast(Any, kernel), [], None, [], cast(Any, {"network_config": {"mode": mode}})
        )

    @pytest.mark.usefixtures("docker")
    async def test_a_seccomp_failure_leaves_the_taken_ports_on_the_kernel(
        self, tmp_path: Path, pool: PortPool
    ) -> None:
        ctx = self._context(tmp_path, pool)
        ctx._apply_seccomp_profile = AsyncMock(side_effect=RuntimeError("no profile"))
        kernel = _StartKernel()

        with pytest.raises(RuntimeError):
            await self._start(ctx, kernel)

        assert kernel["host_ports"] == [30000, 30001]
        assert pool.used_ports() == {30000, 30001}

    async def test_a_cooldown_part_way_leaves_the_ports_already_taken_on_the_kernel(
        self, tmp_path: Path
    ) -> None:
        pool = PortPool((30000, 30001), cooldown_sec=60)
        pool.release(30001)
        ctx = self._context(tmp_path, pool)
        kernel = _StartKernel()

        with pytest.raises(PortPoolExhaustedError):
            await self._start(ctx, kernel)

        assert kernel["host_ports"] == [30000]

    async def test_a_create_that_fails_does_not_release_the_ports_itself(
        self, tmp_path: Path, pool: PortPool, docker: MagicMock
    ) -> None:
        ctx = self._context(tmp_path, pool)
        ctx._apply_seccomp_profile = AsyncMock()
        docker.containers.create = AsyncMock(side_effect=RuntimeError("docker refused"))
        kernel = _StartKernel()

        with pytest.raises(RuntimeError):
            await self._start(ctx, kernel)

        assert kernel["host_ports"] == [30000, 30001]
        assert pool.used_ports() == {30000, 30001}, "released here and again by CLEAN"

    async def test_a_create_cancelled_before_docker_answered_leaves_the_ports_on_the_kernel(
        self, tmp_path: Path, pool: PortPool, docker: MagicMock
    ) -> None:
        ctx = self._context(tmp_path, pool)
        ctx._apply_seccomp_profile = AsyncMock()
        docker.containers.create = AsyncMock(side_effect=asyncio.CancelledError())
        kernel = _StartKernel()

        with pytest.raises(asyncio.CancelledError):
            await self._start(ctx, kernel)

        assert kernel["host_ports"] == [30000, 30001]

    async def test_an_empty_container_id_is_not_recorded(
        self, tmp_path: Path, pool: PortPool, docker: MagicMock
    ) -> None:
        ctx = self._context(tmp_path, pool)
        ctx._apply_seccomp_profile = AsyncMock()
        docker.containers.create = AsyncMock(return_value=SimpleNamespace(_id="", id=""))
        kernel = _StartKernel()

        with pytest.raises(ContainerCreationError) as caught:
            await self._start(ctx, kernel)

        assert caught.value.container_id == ""
        assert "container_id" not in kernel


class _CreatedKernel(_Kernel):
    """The kernel object `prepare_container` returns, as `create_kernel` uses it."""

    def __init__(self) -> None:
        super().__init__(None)
        self.session_type: SessionTypes | None = None

    def set_container_id(self, container_id: ContainerId) -> None:
        self["container_id"] = container_id


class TestCreateKernelWhoseContainerStartFails:
    """Drives `AbstractAgent.create_kernel` itself up to a failing `start_container`."""

    @staticmethod
    def _context(kernel_id: KernelId, start_error: BaseException) -> MagicMock:
        ctx = MagicMock()
        ctx.kernel_id = kernel_id
        ctx.kernel_features = frozenset()
        ctx.get_overriding_uid.return_value = None
        ctx.get_overriding_gid.return_value = None
        ctx.get_supplementary_gids.return_value = []
        ctx.get_extra_envs = AsyncMock(return_value={})
        ctx.image_ref.architecture = "x86_64"
        ctx.image_ref.is_local = True
        resource_spec = MagicMock(mounts=[], allocations={DeviceName("cpu"): {SlotName("cpu"): {}}})
        ctx.generate_resource_spec = AsyncMock(return_value=(resource_spec, {}))
        ctx.get_intrinsic_mounts = AsyncMock(return_value=[])
        for name in (
            "prepare_scratch",
            "destroy_scratch",
            "apply_network",
            "prepare_ssh",
            "mount_vfolders",
            "mount_krunner",
            "inject_additional_device_env_vars",
            "process_mounts",
        ):
            setattr(ctx, name, AsyncMock())
        ctx.kernel_config = {
            "cluster_role": "main",
            "preopen_ports": None,
            "allocated_host_ports": [],
        }
        ctx.prepare_container = AsyncMock(return_value=_CreatedKernel())
        ctx.start_container = AsyncMock(side_effect=start_error)
        return ctx

    @staticmethod
    def _creating_agent(ctx: MagicMock) -> Any:
        local_config = MagicMock()
        local_config.debug.log_kernel_config = False
        local_config.resource.allocation_order = []
        agent = SimpleNamespace(
            _active_creates={},
            local_config=local_config,
            kernel_registry={},
            restarting_kernels={},
            registry_lock=asyncio.Lock(),
            resource_lock=asyncio.Lock(),
            container_lifecycle_queue=asyncio.Queue(),
            computers={
                DeviceName("cpu"): MagicMock(
                    instance=MagicMock(get_attached_devices=AsyncMock(return_value=[]))
                )
            },
            affinity_map=MagicMock(),
            anycast_and_broadcast_event=AsyncMock(),
            init_kernel_context=AsyncMock(return_value=ctx),
            restart_kernel__store_config=AsyncMock(),
            reconstruct_resource_usage=AsyncMock(),
        )
        for name in (
            "track_create",
            "inject_container_lifecycle_event",
            "_unwind_failed_create",
            "_take_back_failed_create",
        ):
            setattr(agent, name, functools.partial(getattr(AbstractAgent, name), cast(Any, agent)))
        return agent

    @pytest.mark.parametrize(
        ("start_error", "container_id"),
        [
            (ContainerCreationError(container_id="cid-1", message="start failed"), "cid-1"),
            (RuntimeError("docker refused"), None),
        ],
        ids=["named-container", "no-container"],
    )
    async def test_exactly_one_destroy_is_queued(
        self, start_error: BaseException, container_id: str | None
    ) -> None:
        kernel_id = KernelId(uuid.uuid4())
        ctx = self._context(kernel_id, start_error)
        agent = self._creating_agent(ctx)
        session_id = SessionId(uuid.uuid4())
        kernel_config = {
            "environ": {},
            "image": {"labels": {}, "digest": "sha256:0", "registry": {}},
            "resource_opts": {},
            "mounts": [],
            "session_type": SessionTypes.INTERACTIVE,
        }

        with (
            patch("ai.backend.agent.agent.get_arch_name", return_value="x86_64"),
            patch("ai.backend.agent.agent.allocate"),
            pytest.raises(ContainerCreationFailedError),
        ):
            await AbstractAgent.create_kernel(
                cast(Any, agent),
                cast(Any, SimpleNamespace(kernel_id=kernel_id, session_id=session_id)),
                MagicMock(),
                cast(Any, kernel_config),
                cast(Any, {}),
            )

        queued: list[ContainerLifecycleEvent] = []
        while not agent.container_lifecycle_queue.empty():
            queued.append(agent.container_lifecycle_queue.get_nowait())
        assert [(ev.event, ev.reason, ev.container_id) for ev in queued] == [
            (LifecycleEvent.DESTROY, KernelLifecycleEventReason.FAILED_TO_CREATE, container_id)
        ]
