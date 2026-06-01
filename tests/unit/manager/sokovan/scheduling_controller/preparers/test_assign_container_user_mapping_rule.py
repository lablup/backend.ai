"""Tests for ``AssignContainerUserMappingRule``."""

from __future__ import annotations

import pytest

from ai.backend.manager.data.session.draft import (
    KernelSpecDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import DefaultSessionOptions
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserInfo,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.assign_container_user_mapping_rule import (
    AssignContainerUserMappingRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)


@pytest.fixture
def rule() -> AssignContainerUserMappingRule:
    return AssignContainerUserMappingRule()


def _context(
    info: ContainerUserInfo | None,
) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
        container_user_info=info,
    )


class TestAssignContainerUserMappingRule:
    async def test_noop_when_context_info_absent(
        self, rule: AssignContainerUserMappingRule
    ) -> None:
        draft = SessionSpecDraft(kernel_specs=(KernelSpecDraft(cluster_role="main"),))
        result = await rule.prepare(draft, _context(None))
        assert result is draft

    async def test_fills_unset_fields_from_context(
        self, rule: AssignContainerUserMappingRule
    ) -> None:
        draft = SessionSpecDraft(
            kernel_specs=(
                KernelSpecDraft(cluster_role="main"),
                KernelSpecDraft(cluster_role="worker"),
            ),
        )
        info = ContainerUserInfo(uid=1000, main_gid=100, supplementary_gids=[200, 300])
        result = await rule.prepare(draft, _context(info))

        for kernel in result.kernel_specs:
            assert kernel.uid == 1000
            assert kernel.main_gid == 100
            assert kernel.supplementary_gids == (200, 300)

    async def test_preserves_caller_set_values(self, rule: AssignContainerUserMappingRule) -> None:
        draft = SessionSpecDraft(
            kernel_specs=(
                KernelSpecDraft(
                    cluster_role="main",
                    uid=2000,
                    main_gid=500,
                    supplementary_gids=(999,),
                ),
            ),
        )
        info = ContainerUserInfo(uid=1000, main_gid=100, supplementary_gids=[200])
        result = await rule.prepare(draft, _context(info))

        kernel = result.kernel_specs[0]
        assert kernel.uid == 2000
        assert kernel.main_gid == 500
        assert kernel.supplementary_gids == (999,)

    async def test_fills_partial_draft(self, rule: AssignContainerUserMappingRule) -> None:
        """A kernel with only ``uid`` set still picks up ``main_gid`` from the context."""
        draft = SessionSpecDraft(
            kernel_specs=(KernelSpecDraft(cluster_role="main", uid=2000),),
        )
        info = ContainerUserInfo(uid=1000, main_gid=100, supplementary_gids=[])
        result = await rule.prepare(draft, _context(info))

        kernel = result.kernel_specs[0]
        assert kernel.uid == 2000
        assert kernel.main_gid == 100
        assert kernel.supplementary_gids == ()
