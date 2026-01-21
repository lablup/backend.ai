"""Tests for ScalingGroupFilter and filter rules."""

from collections.abc import Callable

import pytest

from ai.backend.common.types import SessionTypes
from ai.backend.manager.errors.resource import NoAvailableScalingGroup
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.scaling_group_filter import (
    PublicPrivateFilterRule,
    ScalingGroupFilter,
    SessionTypeFilterRule,
)


class TestPublicPrivateFilterRule:
    """Test cases for PublicPrivateFilterRule."""

    @pytest.fixture
    def public_and_private_groups(self) -> list[AllowedScalingGroup]:
        """Mixed public and private scaling groups."""
        return [
            AllowedScalingGroup(
                name="public-sg",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[SessionTypes.INTERACTIVE, SessionTypes.BATCH]
                ),
            ),
            AllowedScalingGroup(
                name="private-sg",
                is_private=True,
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[SessionTypes.SYSTEM, SessionTypes.BATCH]
                ),
            ),
        ]

    @pytest.fixture
    def public_groups_only(self) -> list[AllowedScalingGroup]:
        """Only public scaling groups."""
        return [
            AllowedScalingGroup(
                name="public-sg-1",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.INTERACTIVE]),
            ),
            AllowedScalingGroup(
                name="public-sg-2",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.BATCH]),
            ),
        ]

    def test_filter_private_groups_for_public_session(
        self,
        public_and_private_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test that private groups are filtered out for public sessions."""
        rule = PublicPrivateFilterRule()
        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,  # Public session
        )

        result = rule.filter(spec, public_and_private_groups)

        # Only public group should pass
        assert len(result.allowed_groups) == 1
        assert result.allowed_groups[0].name == "public-sg"

        # Private group should be rejected
        assert "private-sg" in result.rejected_groups

    def test_allow_private_groups_for_private_session(
        self,
        public_and_private_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test that private groups are allowed for private sessions."""
        rule = PublicPrivateFilterRule()
        spec = session_spec_factory(
            session_type=SessionTypes.SYSTEM,  # Private session
        )

        result = rule.filter(spec, public_and_private_groups)

        # All groups should pass
        assert len(result.allowed_groups) == 2
        assert len(result.rejected_groups) == 0

    def test_allow_all_public_groups(
        self,
        public_groups_only: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test that all public groups pass for public sessions."""
        rule = PublicPrivateFilterRule()
        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,
        )

        result = rule.filter(spec, public_groups_only)

        # All groups should pass
        assert len(result.allowed_groups) == 2
        assert len(result.rejected_groups) == 0


class TestSessionTypeFilterRule:
    """Test cases for SessionTypeFilterRule."""

    @pytest.fixture
    def mixed_session_type_groups(self) -> list[AllowedScalingGroup]:
        """Scaling groups with different session type support."""
        return [
            AllowedScalingGroup(
                name="interactive-only",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.INTERACTIVE]),
            ),
            AllowedScalingGroup(
                name="batch-only",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.BATCH]),
            ),
            AllowedScalingGroup(
                name="all-types",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[
                        SessionTypes.INTERACTIVE,
                        SessionTypes.BATCH,
                        SessionTypes.SYSTEM,
                    ]
                ),
            ),
        ]

    @pytest.mark.parametrize(
        ("session_type", "expected_allowed", "expected_rejected"),
        [
            (
                SessionTypes.INTERACTIVE,
                {"interactive-only", "all-types"},
                {"batch-only"},
            ),
            (
                SessionTypes.BATCH,
                {"batch-only", "all-types"},
                {"interactive-only"},
            ),
            (
                SessionTypes.SYSTEM,
                {"all-types"},
                {"interactive-only", "batch-only"},
            ),
        ],
    )
    def test_filter_by_session_type(
        self,
        mixed_session_type_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
        session_type: SessionTypes,
        expected_allowed: set[str],
        expected_rejected: set[str],
    ) -> None:
        """Test filtering based on session type support."""
        rule = SessionTypeFilterRule()
        spec = session_spec_factory(session_type=session_type)

        result = rule.filter(spec, mixed_session_type_groups)

        # Check allowed groups
        allowed_names = {sg.name for sg in result.allowed_groups}
        assert allowed_names == expected_allowed

        # Check rejected groups
        rejected_names = set(result.rejected_groups.keys())
        assert rejected_names == expected_rejected


class TestScalingGroupFilter:
    """Test cases for ScalingGroupFilter integration."""

    @pytest.fixture
    def comprehensive_scaling_groups(self) -> list[AllowedScalingGroup]:
        """Comprehensive set of scaling groups for integration tests."""
        return [
            AllowedScalingGroup(
                name="public-interactive",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.INTERACTIVE]),
            ),
            AllowedScalingGroup(
                name="public-all-types",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[
                        SessionTypes.INTERACTIVE,
                        SessionTypes.BATCH,
                        SessionTypes.SYSTEM,
                    ]
                ),
            ),
            AllowedScalingGroup(
                name="private-batch",
                is_private=True,
                scheduler_opts=ScalingGroupOpts(
                    allowed_session_types=[SessionTypes.BATCH, SessionTypes.SYSTEM]
                ),
            ),
        ]

    @pytest.fixture
    def filter_with_rules(self) -> ScalingGroupFilter:
        """ScalingGroupFilter with both filter rules."""
        return ScalingGroupFilter([
            PublicPrivateFilterRule(),
            SessionTypeFilterRule(),
        ])

    def test_all_groups_pass_filters(
        self,
        filter_with_rules: ScalingGroupFilter,
        comprehensive_scaling_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test when all groups pass all filters."""
        spec = session_spec_factory(
            session_type=SessionTypes.SYSTEM,  # Private session
        )

        result = filter_with_rules.filter(spec, comprehensive_scaling_groups)

        # Only groups supporting SYSTEM should pass
        # public-interactive doesn't support SYSTEM, so only 2 groups pass
        assert len(result.allowed_groups) == 2
        allowed_names = {sg.name for sg in result.allowed_groups}
        assert "public-all-types" in allowed_names
        assert "private-batch" in allowed_names
        # First allowed group should be auto-selected
        assert result.selected_scaling_group == result.allowed_groups[0].name

    def test_partial_groups_pass_filters(
        self,
        filter_with_rules: ScalingGroupFilter,
        comprehensive_scaling_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test when only some groups pass filters."""
        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,  # Public session
        )

        result = filter_with_rules.filter(spec, comprehensive_scaling_groups)

        # Only public groups supporting INTERACTIVE should pass
        assert len(result.allowed_groups) == 2
        allowed_names = {sg.name for sg in result.allowed_groups}
        assert "public-interactive" in allowed_names
        assert "public-all-types" in allowed_names

    def test_no_groups_pass_filters(
        self,
        filter_with_rules: ScalingGroupFilter,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test when no groups pass filters."""
        # Only interactive-only groups
        scaling_groups = [
            AllowedScalingGroup(
                name="interactive-sg",
                is_private=False,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.INTERACTIVE]),
            ),
        ]

        spec = session_spec_factory(
            session_type=SessionTypes.BATCH,
        )

        with pytest.raises(NoAvailableScalingGroup):
            filter_with_rules.filter(spec, scaling_groups)

    def test_specified_group_filtered_out(
        self,
        filter_with_rules: ScalingGroupFilter,
        comprehensive_scaling_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test when specified scaling group is filtered out."""
        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,  # Public session
            scaling_group="private-batch",  # This will be filtered
        )

        with pytest.raises(NoAvailableScalingGroup):
            filter_with_rules.filter(spec, comprehensive_scaling_groups)

    def test_specified_group_allowed(
        self,
        filter_with_rules: ScalingGroupFilter,
        comprehensive_scaling_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test when specified scaling group passes filters."""
        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="public-all-types",
        )

        result = filter_with_rules.filter(spec, comprehensive_scaling_groups)

        # Specified group should be selected
        assert result.selected_scaling_group == "public-all-types"

    def test_auto_select_when_unspecified(
        self,
        filter_with_rules: ScalingGroupFilter,
        comprehensive_scaling_groups: list[AllowedScalingGroup],
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test auto-selection when scaling group is not specified."""
        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,
            # scaling_group not specified
        )

        result = filter_with_rules.filter(spec, comprehensive_scaling_groups)

        # Selected group should be one of the allowed groups
        allowed_names = {sg.name for sg in result.allowed_groups}
        assert result.selected_scaling_group in allowed_names

    def test_rejected_groups_accumulation(
        self,
        filter_with_rules: ScalingGroupFilter,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test that rejected groups accumulate across multiple rules."""
        scaling_groups = [
            AllowedScalingGroup(
                name="private-interactive",  # Rejected by public/private rule
                is_private=True,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.INTERACTIVE]),
            ),
            AllowedScalingGroup(
                name="public-batch",  # Rejected by session type rule
                is_private=False,
                scheduler_opts=ScalingGroupOpts(allowed_session_types=[SessionTypes.BATCH]),
            ),
        ]

        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,
        )

        with pytest.raises(NoAvailableScalingGroup):
            filter_with_rules.filter(spec, scaling_groups)

    def test_empty_allowed_groups_list(
        self,
        filter_with_rules: ScalingGroupFilter,
        session_spec_factory: Callable[..., SessionCreationSpec],
    ) -> None:
        """Test handling of empty allowed groups list."""
        spec = session_spec_factory(
            session_type=SessionTypes.INTERACTIVE,
        )

        with pytest.raises(NoAvailableScalingGroup):
            filter_with_rules.filter(spec, [])
