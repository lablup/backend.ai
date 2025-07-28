from typing import Sequence

from ai.backend.manager.scheduler.allocators.allocator import SchedulerAllocator
from ai.backend.manager.scheduler.policies.policy import SchedulerPolicy
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class Scheduler:
    _policies: Sequence[SchedulerPolicy]
    _validators: Sequence[SchedulerValidator]
    _allocators: Sequence[SchedulerAllocator]

    def __init__(
        self,
        policies: Sequence[SchedulerPolicy],
        validators: Sequence[SchedulerValidator],
        allocators: Sequence[SchedulerAllocator],
    ):
        self._policies = policies
        self._validators = validators
        self._allocators = allocators

    async def schedule(self) -> None:
        """
        Execute the scheduling process by applying policies,
        validating the state, and allocating resources.
        """
        for policy in self._policies:
            await policy.apply()

        for validator in self._validators:
            await validator.validate()

        for allocator in self._allocators:
            await allocator.allocate()
