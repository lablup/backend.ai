"""Tests for ``InjectSessionEnvironRule``."""

from __future__ import annotations

import pytest

from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypeInfo
from ai.backend.manager.data.session.creation import ContainerUserInfo
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    ResourceSpecDraft,
    SessionOptionsDraft,
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
            default_bootstrap_script=None,
            pending_session_count=0,
            pending_session_resource_slots={},
            vfolder_mounts_by_role={},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={},
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


def _draft_with_sudo(
    *, sudo: bool, kernel_groups: tuple[KernelGroupDraft, ...]
) -> SessionResourceSpecDraft:
    return SessionResourceSpecDraft(
        resource=ResourceSpecDraft(options=SessionOptionsDraft(kernel_groups=kernel_groups)),
        internal_data_extras=InternalDataExtras(sudo_session_enabled=sudo),
    )


class TestInjectSessionEnvironRule:
    async def test_noop_when_sudo_disabled(self, rule: InjectSessionEnvironRule) -> None:
        """Without sudo, the draft is returned unchanged."""
        draft = _draft_with_sudo(
            sudo=False, kernel_groups=(KernelGroupDraft(role="main", replica_count=1),)
        )
        result = await rule.prepare(draft, _context())
        assert result is draft

    async def test_noop_when_no_groups(self, rule: InjectSessionEnvironRule) -> None:
        """With no groups to overlay, the draft is returned unchanged."""
        draft = _draft_with_sudo(sudo=True, kernel_groups=())
        result = await rule.prepare(draft, _context())
        assert result is draft

    async def test_injects_sudo_env_on_every_group(self, rule: InjectSessionEnvironRule) -> None:
        """With sudo enabled, every group's environ carries the flag."""
        draft = _draft_with_sudo(
            sudo=True,
            kernel_groups=(
                KernelGroupDraft(role="main", replica_count=1),
                KernelGroupDraft(role="worker", replica_count=2),
            ),
        )
        result = await rule.prepare(draft, _context())
        groups = result.resource.options.kernel_groups
        assert groups is not None
        for group in groups:
            assert group.execution_spec.environ["SUDO_SESSION_ENABLED"] == "1"

    async def test_preserves_caller_environ_keys(self, rule: InjectSessionEnvironRule) -> None:
        """Caller-set environ entries survive under the overlay."""
        draft = _draft_with_sudo(
            sudo=True,
            kernel_groups=(
                KernelGroupDraft(
                    role="main",
                    replica_count=1,
                    execution_spec=KernelExecutionSpecDraft(environ={"PATH": "/custom/bin"}),
                ),
            ),
        )
        result = await rule.prepare(draft, _context())
        groups = result.resource.options.kernel_groups
        assert groups is not None
        env = groups[0].execution_spec.environ
        assert env["PATH"] == "/custom/bin"
        assert env["SUDO_SESSION_ENABLED"] == "1"
