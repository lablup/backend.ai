from collections.abc import Sequence
from typing import Any, cast

from ai.backend.agent.containerd.runtime.interface import OciRuntime
from ai.backend.agent.health.containerd import ContainerdHealthChecker
from ai.backend.common.health_checker.types import CID_CONTAINERD, CONTAINER


class _FakeRuntime:
    """Just enough of OciRuntime for the liveness probe: list_containers succeeds, or raises to
    emulate an unreachable containerd daemon."""

    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail

    async def list_containers(self) -> Sequence[str]:
        if self._fail:
            raise RuntimeError("containerd unreachable: failed to connect to the gRPC channel")
        return ["c1", "c2"]


def _checker(*, fail: bool = False, timeout: float = 5.0) -> ContainerdHealthChecker:
    return ContainerdHealthChecker(cast(OciRuntime, _FakeRuntime(fail=fail)), timeout=timeout)


class TestContainerdHealthChecker:
    def test_targets_the_container_service_group(self) -> None:
        assert _checker().target_service_group == CONTAINER

    def test_timeout_is_configurable(self) -> None:
        assert _checker(timeout=1.5).timeout == 1.5

    async def test_healthy_when_the_runtime_responds(self) -> None:
        health = await _checker().check_service()
        status = health.results[CID_CONTAINERD]
        assert status.is_healthy is True
        assert status.error_message is None

    async def test_unhealthy_when_the_runtime_errors(self) -> None:
        # a channel/RPC error means the containerd daemon is not reachable; report it, don't raise.
        health = await _checker(fail=True).check_service()
        status = health.results[CID_CONTAINERD]
        assert status.is_healthy is False
        assert status.error_message is not None
        assert "unreachable" in status.error_message

    async def test_check_service_never_raises(self) -> None:
        # the probe must translate failures into an unhealthy status, not propagate them.
        result: Any = await _checker(fail=True).check_service()
        assert CID_CONTAINERD in result.results
