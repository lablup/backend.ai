import hashlib
from types import SimpleNamespace
from typing import Any

from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime, _chain_id


class TestChainId:
    def test_single_layer_is_the_diff_id(self) -> None:
        assert _chain_id(["sha256:aaa"]) == "sha256:aaa"

    def test_empty_is_empty(self) -> None:
        assert _chain_id([]) == ""

    def test_two_layers_fold_with_sha256(self) -> None:
        d0, d1 = "sha256:aaa", "sha256:bbb"
        expected = "sha256:" + hashlib.sha256(f"{d0} {d1}".encode()).hexdigest()
        assert _chain_id([d0, d1]) == expected

    def test_three_layers_fold_left(self) -> None:
        d = ["sha256:a", "sha256:b", "sha256:c"]
        c1 = "sha256:" + hashlib.sha256(b"sha256:a sha256:b").hexdigest()
        c2 = "sha256:" + hashlib.sha256(f"{c1} sha256:c".encode()).hexdigest()
        assert _chain_id(d) == c2

    def test_deterministic(self) -> None:
        d = ["sha256:1", "sha256:2", "sha256:3"]
        assert _chain_id(d) == _chain_id(d)


class TestListContainerInfos:
    def _runtime(self, task_status: str | None) -> Any:
        rt = ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime)

        class _Stub:
            async def List(self, req: Any, metadata: Any = None) -> Any:
                container = SimpleNamespace(id="c1", image="img:1", labels={"k": "v"})
                return SimpleNamespace(containers=[container])

        async def container_status(container_id: str) -> str | None:
            return task_status

        rt._containers_stub = lambda: _Stub()  # type: ignore[method-assign]
        rt.container_status = container_status  # type: ignore[method-assign]
        type(rt)._md = property(lambda self: [])  # type: ignore[assignment]
        return rt

    async def test_container_without_a_task_reports_created(self) -> None:
        # No task => Containers.Create has returned but Tasks.Create has not: the kernel is still
        # being created. Reporting "stopped" here made the agent map it to EXITED, and the
        # lifecycle sync then cleaned a kernel that was mid-creation.
        rt = self._runtime(None)
        infos = await rt.list_container_infos()
        assert infos[0].status == "created"

    async def test_task_status_is_passed_through(self) -> None:
        rt = self._runtime("running")
        infos = await rt.list_container_infos()
        assert infos[0].status == "running"


class TestStopContainer:
    """Graceful stop: SIGTERM, wait for exit, then SIGKILL — Docker's container.stop() parity."""

    def _runtime(self, statuses: list[str | None]) -> tuple[Any, list[int]]:
        rt = ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime)
        signals: list[int] = []
        seq = iter(statuses)

        async def kill_container(container_id: str, *, signal: int) -> None:
            signals.append(signal)

        async def container_status(container_id: str) -> str | None:
            return next(seq, "stopped")

        rt.kill_container = kill_container  # type: ignore[method-assign]
        rt.container_status = container_status  # type: ignore[method-assign]
        return rt, signals

    async def test_sigterm_then_exit_no_sigkill(self) -> None:
        # the task exits on the second poll, so only SIGTERM (15) is sent
        rt, signals = self._runtime(["running", "stopped"])
        await rt.stop_container("c1", grace_period=1.0)
        assert signals == [15]

    async def test_sigkill_when_grace_expires(self) -> None:
        # the task never exits within the grace window -> SIGTERM then SIGKILL
        rt, signals = self._runtime(["running", "running", "running"])
        await rt.stop_container("c1", grace_period=0.15)  # ~1 poll tick
        assert signals == [15, 9]

    async def test_already_gone_is_a_noop_after_sigterm(self) -> None:
        rt, signals = self._runtime([None])
        await rt.stop_container("c1", grace_period=1.0)
        assert signals == [15]  # SIGTERM sent (swallows NOT_FOUND), no SIGKILL
