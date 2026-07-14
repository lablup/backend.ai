"""Tests for ``MergeResourceGroupDefaultsRule``.

Verifies the one-shot RG-default merge that replaces the prior split
``ApplyResourceGroupDefaultsRule`` + ``ApplyDefaultKernelExecutionSpecRule``:

  * option-level defaults (priority / is_preemptible / cluster_mode /
    handler_options / scheduling_target.agent_selection_policy)
  * per-group execution_spec defaults (image_id / resources /
    resource_opts / environ / mounts / startup_command /
    bootstrap_script / starts_at / batch_timeout_sec)
  * caller-supplied values always override the RG baseline
  * empty collections on the draft are treated as "not set"
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import BinarySize, ClusterMode, ResourceSlotEntry
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    KernelResourceInput,
    SchedulingTargetDraft,
    SessionOptionsDraft,
    SessionResourceSpecDraft,
)
from ai.backend.manager.data.session.options import (
    AgentSelectionPolicy,
    DefaultSessionOptions,
    FailurePolicy,
    HandlerOptions,
    KernelExecutionSpec,
    KernelResourceConfig,
    ResourceOpts,
    SessionHandlerOptions,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecPreparationContext,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.merge_resource_group_defaults_rule import (
    MergeResourceGroupDefaultsRule,
)


@pytest.fixture
def rule() -> MergeResourceGroupDefaultsRule:
    return MergeResourceGroupDefaultsRule()


@pytest.fixture
def rg_image_id() -> ImageID:
    return ImageID(uuid.uuid4())


@pytest.fixture
def rg_defaults(rg_image_id: ImageID) -> DefaultSessionOptions:
    return DefaultSessionOptions(
        priority=42,
        is_preemptible=False,
        cluster_mode=ClusterMode.MULTI_NODE,
        default_failure_policy=FailurePolicy.STRICT,
        handler_options=SessionHandlerOptions(
            default=HandlerOptions(timeout=60),
            by_handler={"schedule-sessions": HandlerOptions(max_retry_count=1)},
        ),
        agent_selection_policy=AgentSelectionPolicy.STRICT,
        default_kernel_execution_spec=KernelExecutionSpec(
            resource_input=KernelResourceConfig(
                image_id=rg_image_id,
                resources=[ResourceSlotEntry(resource_type="cpu", quantity="2")],
                resource_opts=ResourceOpts(shmem=BinarySize(128 * 1024 * 1024)),
            ),
            environ={"RG_BASE": "1"},
            startup_command="rg-start",
            bootstrap_script="rg-bootstrap",
        ),
    )


def _context(rg: DefaultSessionOptions) -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(resource_group_defaults=rg)


class TestMergeResourceGroupDefaultsRule:
    async def test_fills_empty_option_fields(
        self,
        rule: MergeResourceGroupDefaultsRule,
        rg_defaults: DefaultSessionOptions,
    ) -> None:
        """Unset option-level fields absorb every RG default."""
        result = await rule.prepare(SessionResourceSpecDraft(), _context(rg_defaults))
        opts = result.options
        assert opts.priority == 42
        assert opts.is_preemptible is False
        assert opts.cluster_mode == ClusterMode.MULTI_NODE
        assert opts.handler_options == SessionHandlerOptions(
            default=HandlerOptions(timeout=60),
            by_handler={"schedule-sessions": HandlerOptions(max_retry_count=1)},
        )
        assert opts.scheduling_target.agent_selection_policy == AgentSelectionPolicy.STRICT

    async def test_preserves_explicit_option_values(
        self,
        rule: MergeResourceGroupDefaultsRule,
        rg_defaults: DefaultSessionOptions,
    ) -> None:
        """Caller-set option-level fields survive the overlay."""
        draft = SessionResourceSpecDraft(
            options=SessionOptionsDraft(
                priority=99,
                cluster_mode=ClusterMode.SINGLE_NODE,
                scheduling_target=SchedulingTargetDraft(
                    agent_selection_policy=AgentSelectionPolicy.PREFERRED,
                ),
            ),
        )
        result = await rule.prepare(draft, _context(rg_defaults))
        opts = result.options
        assert opts.priority == 99
        assert opts.cluster_mode == ClusterMode.SINGLE_NODE
        assert opts.scheduling_target.agent_selection_policy == AgentSelectionPolicy.PREFERRED
        # Unset siblings still filled.
        assert opts.is_preemptible is False

    async def test_fills_group_execution_spec_from_rg_baseline(
        self,
        rule: MergeResourceGroupDefaultsRule,
        rg_defaults: DefaultSessionOptions,
        rg_image_id: ImageID,
    ) -> None:
        """A group without an execution_spec inherits every RG baseline field."""
        draft = SessionResourceSpecDraft(
            options=SessionOptionsDraft(
                kernel_groups=(KernelGroupDraft(role="main", replica_count=1),),
            ),
        )
        result = await rule.prepare(draft, _context(rg_defaults))
        assert result.options.kernel_groups is not None
        merged = result.options.kernel_groups[0].execution_spec
        assert merged.resource_input.image_id == rg_image_id
        assert merged.resource_input.resources == (
            ResourceSlotEntry(resource_type="cpu", quantity="2"),
        )
        assert merged.environ == {"RG_BASE": "1"}
        assert merged.startup_command == "rg-start"
        assert merged.bootstrap_script == "rg-bootstrap"
        assert merged.resource_input.resource_opts == ResourceOpts(
            shmem=BinarySize(128 * 1024 * 1024)
        )

    async def test_preserves_caller_execution_spec_over_rg(
        self,
        rule: MergeResourceGroupDefaultsRule,
        rg_defaults: DefaultSessionOptions,
    ) -> None:
        """Caller-set execution_spec fields win over the RG baseline."""
        caller_image = ImageID(uuid.uuid4())
        draft = SessionResourceSpecDraft(
            options=SessionOptionsDraft(
                kernel_groups=(
                    KernelGroupDraft(
                        role="main",
                        replica_count=1,
                        execution_spec=KernelExecutionSpecDraft(
                            resource_input=KernelResourceInput(
                                image_id=caller_image,
                            ),
                            environ={"CALLER": "yes"},
                        ),
                    ),
                ),
            ),
        )
        result = await rule.prepare(draft, _context(rg_defaults))
        assert result.options.kernel_groups is not None
        merged = result.options.kernel_groups[0].execution_spec
        assert merged.resource_input.image_id == caller_image
        assert merged.environ == {"CALLER": "yes"}
        # Unset fields still picked up from RG.
        assert merged.resource_input.resources == (
            ResourceSlotEntry(resource_type="cpu", quantity="2"),
        )
        assert merged.startup_command == "rg-start"

    async def test_noop_group_merge_when_rg_has_no_default(
        self,
        rule: MergeResourceGroupDefaultsRule,
    ) -> None:
        """With no RG default_kernel_execution_spec, only option-level fill happens."""
        rg = DefaultSessionOptions(priority=7)
        draft = SessionResourceSpecDraft(
            options=SessionOptionsDraft(
                kernel_groups=(KernelGroupDraft(role="main", replica_count=1),),
            ),
        )
        result = await rule.prepare(draft, _context(rg))
        assert result.options.priority == 7
        assert result.options.kernel_groups is not None
        assert result.options.kernel_groups[0].execution_spec.resource_input.image_id is None
