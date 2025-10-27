"""Scaling group filtering for session creation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import override

from ai.backend.manager.errors.resource import NoAvailableScalingGroup
from ai.backend.manager.models import PRIVATE_SESSION_TYPES
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationSpec,
)

from .base import (
    ScalingGroupFilterResult,
    ScalingGroupFilterRule,
    ScalingGroupFilterRuleResult,
)


class PublicPrivateFilterRule(ScalingGroupFilterRule):
    """Filters out private scaling groups for public sessions."""

    @override
    def name(self) -> str:
        return "public_private_filter"

    @override
    def filter(
        self,
        spec: SessionCreationSpec,
        allowed_groups: list[AllowedScalingGroup],
    ) -> ScalingGroupFilterRuleResult:
        public_sgroup_only = spec.session_type not in PRIVATE_SESSION_TYPES
        filtered_groups: list[AllowedScalingGroup] = []
        rejected_groups: dict[str, str] = {}

        for sg in allowed_groups:
            if public_sgroup_only and sg.is_private:
                rejected_groups[sg.name] = (
                    f"Private scaling group not allowed for {spec.session_type.value} sessions"
                )
            else:
                filtered_groups.append(sg)

        return ScalingGroupFilterRuleResult(
            allowed_groups=filtered_groups,
            rejected_groups=rejected_groups,
        )


class SessionTypeFilterRule(ScalingGroupFilterRule):
    """Filters out scaling groups that don't support the requested session type."""

    @override
    def name(self) -> str:
        return "session_type_filter"

    @override
    def filter(
        self,
        spec: SessionCreationSpec,
        allowed_groups: list[AllowedScalingGroup],
    ) -> ScalingGroupFilterRuleResult:
        filtered_groups: list[AllowedScalingGroup] = []
        rejected_groups: dict[str, str] = {}

        for sg in allowed_groups:
            if spec.session_type not in sg.scheduler_opts.allowed_session_types:
                allowed_types = ", ".join([
                    st.value for st in sg.scheduler_opts.allowed_session_types
                ])
                rejected_groups[sg.name] = (
                    f"Session type {spec.session_type.value} not allowed (allowed: {allowed_types})"
                )
            else:
                filtered_groups.append(sg)

        return ScalingGroupFilterRuleResult(
            allowed_groups=filtered_groups,
            rejected_groups=rejected_groups,
        )


class ScalingGroupFilter:
    """
    Filters scaling groups by applying multiple filter rules.

    Each rule filters the list sequentially, and rejected groups
    accumulate across all rules.
    """

    _rules: Iterable[ScalingGroupFilterRule]

    def __init__(self, rules: Iterable[ScalingGroupFilterRule]) -> None:
        self._rules = rules

    def filter(
        self,
        spec: SessionCreationSpec,
        allowed_groups: list[AllowedScalingGroup],
    ) -> ScalingGroupFilterResult:
        """
        Filter scaling groups by applying all rules sequentially and validate the result.

        Args:
            spec: Session creation specification
            allowed_groups: List of scaling groups allowed for the user

        Returns:
            ScalingGroupFilterResult containing groups that passed all filters

        Raises:
            NoAvailableScalingGroup: If no scaling groups pass the filters,
                or if the specified scaling group is not in the filtered list
        """
        current_groups = allowed_groups
        all_rejected: dict[str, str] = {}

        for rule in self._rules:
            result = rule.filter(spec, current_groups)
            current_groups = result.allowed_groups
            all_rejected.update(result.rejected_groups)

        # Check if any scaling groups passed all filters
        if not current_groups:
            error_lines = ["No scaling groups available for this session."]
            if all_rejected:
                error_lines.append("Rejected scaling groups:")
                for sg_name, reason in all_rejected.items():
                    error_lines.append(f"  - {sg_name}: {reason}")
            raise NoAvailableScalingGroup("\n".join(error_lines))

        # Select scaling group
        # If scaling_group is specified, verify it's in the filtered list
        if spec.scaling_group:
            filtered_names = {sg.name for sg in current_groups}
            if spec.scaling_group not in filtered_names:
                rejection_reason = all_rejected.get(
                    spec.scaling_group,
                    "Not in allowed scaling groups",
                )
                raise NoAvailableScalingGroup(
                    f"Scaling group {spec.scaling_group} cannot be used: {rejection_reason}"
                )
            return ScalingGroupFilterResult(
                allowed_groups=current_groups,
                selected_scaling_group=spec.scaling_group,
            )

        # If not specified, select the first one from filtered list
        return ScalingGroupFilterResult(
            allowed_groups=current_groups,
            selected_scaling_group=current_groups[0].name,
        )
