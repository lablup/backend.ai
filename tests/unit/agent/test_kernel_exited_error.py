from __future__ import annotations

from ai.backend.agent.errors.agent import ContainerCreationFailedError, KernelExitedBeforeReadyError
from ai.backend.agent.errors.containerd import KernelTaskExited


class TestKernelExitedBeforeReadyError:
    def test_containerd_error_is_caught_as_the_backend_neutral_base(self) -> None:
        err = KernelTaskExited("gone", exit_status=137, failure_reason="named")

        assert isinstance(err, KernelExitedBeforeReadyError)
        assert err.exit_status == 137

    def test_failure_reason_prefix_is_shared_with_the_creation_error(self) -> None:
        exited = KernelExitedBeforeReadyError("detail", failure_reason="named")
        failed = ContainerCreationFailedError("detail", failure_reason="named")

        assert str(exited).endswith("(named: detail)")
        assert str(failed).endswith("(named: detail)")
