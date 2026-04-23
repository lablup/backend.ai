"""Tests for ``InjectSessionEnvironRule``."""

from __future__ import annotations

import pytest

from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelSpecDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    InternalDataInputs,
    SessionSpecPreparationContext,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.inject_session_environ_rule import (
    InjectSessionEnvironRule,
)


@pytest.fixture
def rule() -> InjectSessionEnvironRule:
    return InjectSessionEnvironRule()


def _context(*, sudo: bool) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        internal_data_inputs=InternalDataInputs(sudo_session_enabled=sudo),
    )


class TestInjectSessionEnvironRule:
    async def test_noop_when_sudo_disabled(self, rule: InjectSessionEnvironRule) -> None:
        """Without sudo, the draft is returned unchanged."""
        draft = SessionSpecDraft(kernel_specs=(KernelSpecDraft(cluster_role="main"),))
        result = await rule.prepare(draft, _context(sudo=False))
        assert result is draft

    async def test_injects_sudo_env_on_every_kernel(self, rule: InjectSessionEnvironRule) -> None:
        """With sudo enabled, every kernel's environ carries the flag."""
        draft = SessionSpecDraft(
            kernel_specs=(
                KernelSpecDraft(cluster_role="main"),
                KernelSpecDraft(cluster_role="worker"),
            ),
        )
        result = await rule.prepare(draft, _context(sudo=True))
        for kernel in result.kernel_specs:
            assert kernel.execution_spec.environ["SUDO_SESSION_ENABLED"] == "1"

    async def test_preserves_caller_environ_keys(self, rule: InjectSessionEnvironRule) -> None:
        """Caller-set environ entries survive under the overlay."""
        draft = SessionSpecDraft(
            kernel_specs=(
                KernelSpecDraft(
                    cluster_role="main",
                    execution_spec=KernelExecutionSpecDraft(
                        environ={"PATH": "/custom/bin"},
                    ),
                ),
            ),
        )
        result = await rule.prepare(draft, _context(sudo=True))
        env = result.kernel_specs[0].execution_spec.environ
        assert env["PATH"] == "/custom/bin"
        assert env["SUDO_SESSION_ENABLED"] == "1"
