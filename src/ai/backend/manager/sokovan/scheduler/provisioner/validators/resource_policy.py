"""Validator for per-scope resource policies (slot quotas and session-count caps)."""

from typing import override

from ai.backend.manager.views.sokovan.snapshot import (
    ResourceAllocation,
    SystemSnapshot,
    UserResourceAllocation,
)
from ai.backend.manager.views.sokovan.workload import SessionWorkload

from .exceptions import (
    ConcurrencyLimitExceeded,
    DomainResourceQuotaExceeded,
    MultipleValidationErrors,
    ProjectResourceQuotaExceeded,
    SchedulingValidationError,
    UserResourceQuotaExceeded,
)
from .validator import ValidatorRule


class ResourcePolicyValidator(ValidatorRule):
    """
    Check the workload against the user, project, and domain resource policies:
    slot quotas for every scope plus the user's concurrent-session caps.
    Corresponds to the check_concurrency and check_user/group/domain_resource_limit
    predicates.

    All scopes are checked so that every violated quota is reported, not
    just the first one.
    """

    @override
    def name(self) -> str:
        """Return the validator name for predicates."""
        return "ResourcePolicyValidator"

    @override
    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Requested resources are within the user, project, and domain resource policies"

    @override
    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        policy = snapshot.global_scope.resource_policy
        occupancy = snapshot.global_scope.occupancy
        request = workload.requested_slots
        errors: list[SchedulingValidationError] = []

        # A missing limit means the scope imposes no quota
        user_limit = policy.by_user.get(workload.user_uuid)
        if user_limit is not None:
            user_allocation = occupancy.by_user.get(
                workload.user_uuid, UserResourceAllocation.empty()
            )
            if user_allocation.exceeds(request, user_limit):
                errors.append(UserResourceQuotaExceeded(quota_slots=user_limit.slots))
            if user_allocation.count_exceeds(request, user_limit):
                if workload.is_private:
                    max_count, session_type = user_limit.max_sftp_session_count, "SFTP"
                else:
                    max_count, session_type = user_limit.max_session_count, "concurrent"
                errors.append(
                    ConcurrencyLimitExceeded(
                        max_sessions=max_count or 0,
                        session_type=session_type,
                    )
                )

        project_limit = policy.by_project.get(workload.project_id)
        if project_limit is not None:
            project_allocation = occupancy.by_project.get(
                workload.project_id, ResourceAllocation.empty()
            )
            if project_allocation.exceeds(request, project_limit):
                errors.append(ProjectResourceQuotaExceeded(quota_slots=project_limit.slots))

        domain_limit = policy.by_domain.get(workload.domain_id)
        if domain_limit is not None:
            domain_allocation = occupancy.by_domain.get(
                workload.domain_id, ResourceAllocation.empty()
            )
            if domain_allocation.exceeds(request, domain_limit):
                errors.append(DomainResourceQuotaExceeded(quota_slots=domain_limit.slots))

        if errors:
            if len(errors) == 1:
                raise errors[0]
            raise MultipleValidationErrors(errors)
