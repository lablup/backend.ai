"""Tests for ``InjectSessionEnvironRule``."""

from __future__ import annotations

import pytest

from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypeInfo
from ai.backend.manager.data.session.creation import ContainerUserInfo
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelSpecDraft,
    ResourceSpecDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.options import (
    DefaultSessionOptions,
    InternalDataExtras,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.specs.inject_session_environ_rule import (
    InjectSessionEnvironRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
    UserEnqueueInfo,
)


@pytest.fixture
def rule() -> InjectSessionEnvironRule:
    return InjectSessionEnvironRule()


def _context() -> SessionSpecContext:
    return SessionSpecContext(
        resource_group=ResourceGroupEnqueueInfo(
            defaults=DefaultSessionOptions(),
            network=None,
            allow_fractional=False,
            served_slot_names=frozenset(),
        ),
        user=UserEnqueueInfo(
            policy=None,
            container_user=ContainerUserInfo(),
            dotfiles=DotfileBundle(),
            pending_session_count=0,
            vfolder_mounts_by_role={},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={},
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


def _draft_with_sudo(
    *, sudo: bool, kernel_specs: tuple[KernelSpecDraft, ...]
) -> SessionResourceSpecDraft:
    return SessionResourceSpecDraft(
        resource=ResourceSpecDraft(kernel_specs=kernel_specs),
        internal_data_extras=InternalDataExtras(sudo_session_enabled=sudo),
    )


class TestInjectSessionEnvironRule:
    async def test_noop_when_sudo_disabled(self, rule: InjectSessionEnvironRule) -> None:
        """Without sudo, the draft is returned unchanged."""
        draft = _draft_with_sudo(sudo=False, kernel_specs=(KernelSpecDraft(cluster_role="main"),))
        result = await rule.prepare(draft, _context())
        assert result is draft

    async def test_injects_sudo_env_on_every_kernel(self, rule: InjectSessionEnvironRule) -> None:
        """With sudo enabled, every kernel's environ carries the flag."""
        draft = _draft_with_sudo(
            sudo=True,
            kernel_specs=(
                KernelSpecDraft(cluster_role="main"),
                KernelSpecDraft(cluster_role="worker"),
            ),
        )
        result = await rule.prepare(draft, _context())
        for kernel in result.resource.kernel_specs:
            assert kernel.execution_spec.environ["SUDO_SESSION_ENABLED"] == "1"

    async def test_preserves_caller_environ_keys(self, rule: InjectSessionEnvironRule) -> None:
        """Caller-set environ entries survive under the overlay."""
        draft = _draft_with_sudo(
            sudo=True,
            kernel_specs=(
                KernelSpecDraft(
                    cluster_role="main",
                    execution_spec=KernelExecutionSpecDraft(
                        environ={"PATH": "/custom/bin"},
                    ),
                ),
            ),
        )
        result = await rule.prepare(draft, _context())
        env = result.resource.kernel_specs[0].execution_spec.environ
        assert env["PATH"] == "/custom/bin"
        assert env["SUDO_SESSION_ENABLED"] == "1"
