"""Validator for domain resource limits."""

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import DomainResourceQuotaExceeded
from .validator import ValidatorRule


class DomainResourceLimitValidator(ValidatorRule):
    """
    Check if a session would exceed the domain's resource quota.
    This corresponds to check_domain_resource_limit predicate.
    """

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "DomainResourceLimitValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "Domain has sufficient resource quota for the requested session"

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get the domain's resource limit
        domain_limit = snapshot.resource_policy.domain_limits.get(workload.domain_name)
        if not domain_limit:
            # If no limit is defined, we can't validate - let it pass
            return

        # Get current domain occupancy
        domain_occupied = snapshot.resource_occupancy.by_domain.get(
            workload.domain_name, ResourceSlot()
        )

        # Check if adding this workload would exceed the limit
        total_after = domain_occupied + workload.requested_slots
        if not (total_after <= domain_limit):
            # Format the limit for human-readable output
            if domain_limit and any(v for v in domain_limit.values()):
                limit_str = " ".join(f"{k}={v}" for k, v in domain_limit.items() if v)
                exceeded_msg = f"limit: {limit_str}, current: {domain_occupied}, requested: {workload.requested_slots}"
            else:
                exceeded_msg = f"No resource limits defined. current: {domain_occupied}, requested: {workload.requested_slots}"
            raise DomainResourceQuotaExceeded(
                f"Your domain resource quota is exceeded. ({exceeded_msg})"
            )
