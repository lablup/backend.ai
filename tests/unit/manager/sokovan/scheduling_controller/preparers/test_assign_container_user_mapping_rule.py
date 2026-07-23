"""Tests for ``AssignContainerUserMappingRule``."""

from __future__ import annotations

import pytest

from ai.backend.manager.data.dotfile.types import DotfileBundle
from ai.backend.manager.data.resource.types import SlotTypeInfo
from ai.backend.manager.data.session.creation import ContainerUserInfo
from ai.backend.manager.data.session.draft import (
    KernelSpecDraft,
    ResourceSpecDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.sokovan.scheduling_controller.preparers.specs.assign_container_user_mapping_rule import (
    AssignContainerUserMappingRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    GlobalEnqueueInfo,
    ResourceGroupEnqueueInfo,
    SessionSpecContext,
    UserEnqueueInfo,
)


@pytest.fixture
def rule() -> AssignContainerUserMappingRule:
    return AssignContainerUserMappingRule()


def _context(info: ContainerUserInfo) -> SessionSpecContext:
    return SessionSpecContext(
        resource_group=ResourceGroupEnqueueInfo(
            defaults=DefaultSessionOptions(),
            network=None,
            allow_fractional=False,
            served_slot_names=frozenset(),
        ),
        user=UserEnqueueInfo(
            policy=None,
            container_user=info,
            dotfiles=DotfileBundle(),
            pending_session_count=0,
            vfolder_mounts_by_role={},
        ),
        global_info=GlobalEnqueueInfo(
            image_infos={},
            slot_type_info=SlotTypeInfo(types={}, required=frozenset()),
        ),
    )


def _draft(*kernels: KernelSpecDraft) -> SessionResourceSpecDraft:
    return SessionResourceSpecDraft(resource=ResourceSpecDraft(kernel_specs=kernels))


class TestAssignContainerUserMappingRule:
    async def test_keeps_fields_unset_when_context_info_empty(
        self, rule: AssignContainerUserMappingRule
    ) -> None:
        """An all-None context info leaves the kernel fields unset."""
        draft = _draft(KernelSpecDraft(cluster_role="main"))
        result = await rule.prepare(draft, _context(ContainerUserInfo()))
        kernel = result.resource.kernel_specs[0]
        assert kernel.uid is None
        assert kernel.main_gid is None
        assert kernel.supplementary_gids == ()

    async def test_fills_unset_fields_from_context(
        self, rule: AssignContainerUserMappingRule
    ) -> None:
        draft = _draft(
            KernelSpecDraft(cluster_role="main"),
            KernelSpecDraft(cluster_role="worker"),
        )
        info = ContainerUserInfo(uid=1000, main_gid=100, supplementary_gids=[200, 300])
        result = await rule.prepare(draft, _context(info))

        for kernel in result.resource.kernel_specs:
            assert kernel.uid == 1000
            assert kernel.main_gid == 100
            assert kernel.supplementary_gids == (200, 300)

    async def test_preserves_caller_set_values(self, rule: AssignContainerUserMappingRule) -> None:
        draft = _draft(
            KernelSpecDraft(
                cluster_role="main",
                uid=2000,
                main_gid=500,
                supplementary_gids=(999,),
            ),
        )
        info = ContainerUserInfo(uid=1000, main_gid=100, supplementary_gids=[200])
        result = await rule.prepare(draft, _context(info))

        kernel = result.resource.kernel_specs[0]
        assert kernel.uid == 2000
        assert kernel.main_gid == 500
        assert kernel.supplementary_gids == (999,)

    async def test_fills_partial_draft(self, rule: AssignContainerUserMappingRule) -> None:
        """A kernel with only ``uid`` set still picks up ``main_gid`` from the context."""
        draft = _draft(KernelSpecDraft(cluster_role="main", uid=2000))
        info = ContainerUserInfo(uid=1000, main_gid=100, supplementary_gids=[])
        result = await rule.prepare(draft, _context(info))

        kernel = result.resource.kernel_specs[0]
        assert kernel.uid == 2000
        assert kernel.main_gid == 100
        assert kernel.supplementary_gids == ()
