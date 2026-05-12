"""Tests for ``SessionSpecPreparer``.

Covers two concerns:

* the rule-chain runner — rules execute in declaration order, each
  receives the output of the previous, and the final draft is
  projected into a frozen :class:`SessionSpec`.
* the finalization projection — empty / partially-populated drafts
  surface precise attribute paths, Optional spec fields default to
  ``None`` when the draft leaves them unset, and nested / list paths
  report correctly.

Finalization is exercised by invoking the preparer with an empty rule
chain, which makes the projection step the only behavior under test.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest

from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.types import AccessKey, ClusterMode, ResourceSlotEntry, SessionTypes
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    KernelSpecDraft,
    SessionClassificationDraft,
    SessionIdentityDraft,
    SessionNetworkDraft,
    SessionOptionsDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import (
    DefaultSessionOptions,
    SessionHandlerOptions,
)
from ai.backend.manager.errors.kernel import IncompleteSessionSpec
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.scheduling_controller.preparers.draft_rule import (
    SessionSpecDraftRule,
    SessionSpecPreparationContext,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.merge_resource_group_defaults_rule import (
    MergeResourceGroupDefaultsRule,
)
from ai.backend.manager.sokovan.scheduling_controller.preparers.session_spec_preparer import (
    SessionSpecPreparer,
)


class _TransformRule(SessionSpecDraftRule):
    """Stub rule: records invocation order on a shared log and applies a callable."""

    def __init__(
        self,
        tag: str,
        log: list[str],
        transform: Callable[[SessionSpecDraft], SessionSpecDraft],
    ) -> None:
        self._tag = tag
        self._log = log
        self._transform = transform

    def name(self) -> str:
        return self._tag

    async def prepare(
        self,
        draft: SessionSpecDraft,
        context: SessionSpecPreparationContext,
    ) -> SessionSpecDraft:
        self._log.append(self._tag)
        return self._transform(draft)


@pytest.fixture
def context() -> SessionSpecPreparationContext:
    return SessionSpecPreparationContext(
        resource_group_defaults=DefaultSessionOptions(),
    )


@pytest.fixture
def image_id() -> ImageID:
    return ImageID(uuid.uuid4())


@pytest.fixture
def minimal_kernel_group(image_id: ImageID) -> KernelGroupDraft:
    return KernelGroupDraft(
        role="main",
        replica_count=1,
        execution_spec=KernelExecutionSpecDraft(
            image_id=image_id,
            resources=(ResourceSlotEntry(resource_type="cpu", quantity="1"),),
        ),
    )


@pytest.fixture
def complete_draft(image_id: ImageID, minimal_kernel_group: KernelGroupDraft) -> SessionSpecDraft:
    """A finalize-ready draft for tests that only care about the happy path."""
    return SessionSpecDraft(
        identity=SessionIdentityDraft(
            session_id=SessionID(uuid.uuid4()),
            creation_id="test-creation-id",
            session_name="test-session",
            access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
            user_uuid=uuid.uuid4(),
        ),
        scope=SessionScopeDraft(
            domain_name=DomainName("default"),
            project_id=ProjectID(uuid.uuid4()),
            resource_group_name=ResourceGroupName("default"),
        ),
        classification=SessionClassificationDraft(
            session_type=SessionTypes.INTERACTIVE,
        ),
        network=SessionNetworkDraft(
            network_type=NetworkType.VOLATILE,
        ),
        options=SessionOptionsDraft(
            priority=10,
            is_preemptible=True,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
            kernel_groups=(minimal_kernel_group,),
            handler_options=SessionHandlerOptions(),
        ),
        kernel_specs=(
            KernelSpecDraft(
                cluster_role="main",
                cluster_idx=1,
                cluster_hostname="main1",
                local_rank=0,
                execution_spec=KernelExecutionSpecDraft(
                    image_id=image_id,
                    resources=(ResourceSlotEntry(resource_type="cpu", quantity="1"),),
                ),
            ),
        ),
    )


class TestRuleChain:
    """Exercises the ordered-rule-chain behavior of the runner."""

    async def test_empty_rule_chain_just_finalizes(
        self,
        context: SessionSpecPreparationContext,
        complete_draft: SessionSpecDraft,
    ) -> None:
        """With no rules, the input draft must already be finalize-ready."""
        preparer = SessionSpecPreparer([])
        spec = await preparer.prepare(complete_draft, context)
        assert spec.identity.session_name == "test-session"

    async def test_runs_rules_in_declaration_order(
        self,
        context: SessionSpecPreparationContext,
        complete_draft: SessionSpecDraft,
    ) -> None:
        """Rules execute in the order they are passed to the constructor."""
        log: list[str] = []
        preparer = SessionSpecPreparer([
            _TransformRule("A", log, lambda d: d),
            _TransformRule("B", log, lambda d: d),
            _TransformRule("C", log, lambda d: d),
        ])
        await preparer.prepare(complete_draft, context)
        assert log == ["A", "B", "C"]

    async def test_rule_output_feeds_next_rule(
        self,
        context: SessionSpecPreparationContext,
    ) -> None:
        """Each rule sees the draft emitted by the previous rule."""
        log: list[str] = []

        def set_priority(d: SessionSpecDraft) -> SessionSpecDraft:
            return d.model_copy(update={"options": d.options.model_copy(update={"priority": 7})})

        captured: dict[str, int | None] = {}

        def capture_priority(d: SessionSpecDraft) -> SessionSpecDraft:
            captured["priority"] = d.options.priority
            return d

        preparer = SessionSpecPreparer([
            _TransformRule("set", log, set_priority),
            _TransformRule("capture", log, capture_priority),
        ])
        with pytest.raises(IncompleteSessionSpec):
            # Draft stays incomplete (identity / scope / etc. still
            # unset), but the rule chain runs to completion first.
            await preparer.prepare(SessionSpecDraft(), context)

        assert captured["priority"] == 7
        assert log == ["set", "capture"]

    async def test_end_to_end_with_real_rule(
        self,
        context: SessionSpecPreparationContext,
        complete_draft: SessionSpecDraft,
    ) -> None:
        """``MergeResourceGroupDefaultsRule`` wired through the runner fills
        unset options and produces a valid ``SessionSpec``."""
        draft = complete_draft.model_copy(
            update={"options": complete_draft.options.model_copy(update={"priority": None})}
        )
        preparer = SessionSpecPreparer([MergeResourceGroupDefaultsRule()])
        spec = await preparer.prepare(draft, context)
        # RG default for priority is 10 (DefaultSessionOptions.priority default).
        assert spec.options.priority == 10


class TestFinalization:
    """Exercises draft → spec projection via the empty-chain preparer."""

    @pytest.fixture
    def preparer(self) -> SessionSpecPreparer:
        return SessionSpecPreparer([])

    async def test_empty_draft_raises_with_required_paths(
        self,
        preparer: SessionSpecPreparer,
        context: SessionSpecPreparationContext,
    ) -> None:
        """An empty draft surfaces every required-spec field as a missing path."""
        with pytest.raises(IncompleteSessionSpec) as exc_info:
            await preparer.prepare(SessionSpecDraft(), context)
        extra_data = exc_info.value.extra_data
        assert extra_data is not None
        missing: list[str] = extra_data["missing"]
        # Representative sample from every grouping.
        assert "identity.session_id" in missing
        assert "identity.creation_id" in missing
        assert "identity.session_name" in missing
        assert "identity.access_key" in missing
        assert "identity.user_uuid" in missing
        assert "scope.domain_name" in missing
        assert "scope.project_id" in missing
        assert "scope.resource_group_name" in missing
        assert "classification.session_type" in missing
        assert "network.network_type" in missing
        assert "options.priority" in missing
        assert "options.is_preemptible" in missing
        assert "options.cluster_mode" in missing
        assert "options.cluster_size" in missing
        assert "options.kernel_groups" in missing
        assert "options.handler_options" in missing

    async def test_complete_draft_projects_to_session_spec(
        self,
        preparer: SessionSpecPreparer,
        context: SessionSpecPreparationContext,
        complete_draft: SessionSpecDraft,
    ) -> None:
        """A fully populated draft projects cleanly into a SessionSpec."""
        spec = await preparer.prepare(complete_draft, context)

        assert spec.identity.session_name == "test-session"
        assert spec.identity.access_key == AccessKey("AKIAIOSFODNN7EXAMPLE")
        assert spec.scope.domain_name == DomainName("default")
        assert spec.scope.resource_group_name == ResourceGroupName("default")
        assert spec.classification.session_type == SessionTypes.INTERACTIVE
        assert spec.options.priority == 10
        assert spec.options.cluster_mode == ClusterMode.SINGLE_NODE
        assert spec.options.cluster_size == 1
        assert len(spec.options.kernel_groups) == 1
        assert spec.options.kernel_groups[0].role == "main"
        assert len(spec.kernel_specs) == 1
        assert spec.kernel_specs[0].cluster_role == "main"
        assert spec.kernel_specs[0].cluster_idx == 1
        assert spec.kernel_specs[0].cluster_hostname == "main1"

    async def test_optional_spec_fields_default_to_none(
        self,
        preparer: SessionSpecPreparer,
        context: SessionSpecPreparationContext,
        complete_draft: SessionSpecDraft,
    ) -> None:
        """Optional spec fields not set on the draft land as None on the spec."""
        spec = await preparer.prepare(complete_draft, context)
        assert spec.classification.tag is None
        assert spec.kernel_specs[0].uid is None
        assert spec.kernel_specs[0].main_gid is None
        assert spec.kernel_specs[0].supplementary_gids == ()
        assert spec.kernel_specs[0].execution_spec.startup_command is None
        assert spec.kernel_specs[0].execution_spec.bootstrap_script is None

    async def test_partial_identity_reports_only_unset_paths(
        self,
        preparer: SessionSpecPreparer,
        context: SessionSpecPreparationContext,
    ) -> None:
        """Only genuinely unset fields surface; set fields stay off the list."""
        draft = SessionSpecDraft(
            identity=SessionIdentityDraft(
                session_id=SessionID(uuid.uuid4()),
                # session_name intentionally unset
                access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
            ),
        )
        with pytest.raises(IncompleteSessionSpec) as exc_info:
            await preparer.prepare(draft, context)
        extra_data = exc_info.value.extra_data
        assert extra_data is not None
        missing: list[str] = extra_data["missing"]
        assert "identity.session_name" in missing
        assert "identity.session_id" not in missing
        assert "identity.access_key" not in missing

    async def test_kernel_specs_element_path_is_indexed(
        self,
        preparer: SessionSpecPreparer,
        context: SessionSpecPreparationContext,
        complete_draft: SessionSpecDraft,
        image_id: ImageID,
    ) -> None:
        """Missing fields inside a ``kernel_specs`` entry report with index."""
        broken_kernel = KernelSpecDraft(
            # cluster_role intentionally unset
            cluster_idx=1,
            cluster_hostname="main1",
            local_rank=0,
            execution_spec=KernelExecutionSpecDraft(
                image_id=image_id,
                resources=(ResourceSlotEntry(resource_type="cpu", quantity="1"),),
            ),
        )
        draft = complete_draft.model_copy(update={"kernel_specs": (broken_kernel,)})
        with pytest.raises(IncompleteSessionSpec) as exc_info:
            await preparer.prepare(draft, context)
        extra_data = exc_info.value.extra_data
        assert extra_data is not None
        missing: list[str] = extra_data["missing"]
        assert "kernel_specs[0].cluster_role" in missing

    async def test_kernel_execution_spec_nested_path(
        self,
        preparer: SessionSpecPreparer,
        context: SessionSpecPreparationContext,
        complete_draft: SessionSpecDraft,
    ) -> None:
        """Missing fields inside an ``execution_spec`` sub-draft report the full path."""
        broken_kernel = KernelSpecDraft(
            cluster_role="main",
            cluster_idx=1,
            cluster_hostname="main1",
            local_rank=0,
            execution_spec=KernelExecutionSpecDraft(
                # image_id intentionally unset
                resources=(ResourceSlotEntry(resource_type="cpu", quantity="1"),),
            ),
        )
        draft = complete_draft.model_copy(update={"kernel_specs": (broken_kernel,)})
        with pytest.raises(IncompleteSessionSpec) as exc_info:
            await preparer.prepare(draft, context)
        extra_data = exc_info.value.extra_data
        assert extra_data is not None
        missing: list[str] = extra_data["missing"]
        assert "kernel_specs[0].execution_spec.image_id" in missing
