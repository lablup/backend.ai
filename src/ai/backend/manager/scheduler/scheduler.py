from typing import Mapping, Optional, Sequence

from ai.backend.common.types import AgentId, ResourceSlot, SessionId, SlotName, SlotTypes
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models import AgentRow
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.scheduler.allocators.allocator import SchedulerAllocator
from ai.backend.manager.scheduler.policies.policy import SchedulerPolicy
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class Scheduler:
    _policy: SchedulerPolicy  # Changed to single policy
    _validators: Sequence[SchedulerValidator]
    _allocator: SchedulerAllocator  # Changed to single allocator
    _session_repository: SessionRepository
    _user_repository: UserRepository
    _group_repository: GroupRepository
    _domain_repository: DomainRepository
    _known_slot_types: Mapping[SlotName, SlotTypes]

    def __init__(
        self,
        policy: SchedulerPolicy,
        validators: Sequence[SchedulerValidator],
        allocator: SchedulerAllocator,
        session_repository: SessionRepository,
        user_repository: UserRepository,
        group_repository: GroupRepository,
        domain_repository: DomainRepository,
        known_slot_types: Mapping[SlotName, SlotTypes],
    ):
        self._policy = policy
        self._validators = validators
        self._allocator = allocator
        self._session_repository = session_repository
        self._user_repository = user_repository
        self._group_repository = group_repository
        self._domain_repository = domain_repository
        self._known_slot_types = known_slot_types

    async def _create_validator_context(self, session_data: SessionData) -> ValidatorContext:
        """Create ValidatorContext by fetching necessary data from repositories."""
        # Fetch session-related data
        session_starts_at = None
        if session_data.starts_at:
            session_starts_at = session_data.starts_at

        session_dependencies = await self._session_repository.get_session_dependencies(
            session_data.id
        )
        pending_sessions = await self._session_repository.get_pending_sessions(
            session_data.access_key
        )

        # Fetch resource policies
        keypair_resource_policy = await self._user_repository.get_keypair_resource_policy(
            session_data.access_key
        )
        user_main_keypair_resource_policy = (
            await self._user_repository.get_user_main_keypair_resource_policy(
                session_data.user_uuid
            )
        )
        group_resource_policy = await self._group_repository.get_group_resource_policy(
            session_data.group_id
        )
        domain_resource_policy = await self._domain_repository.get_domain_resource_policy(
            session_data.domain_name
        )

        # Fetch current resource usage
        keypair_concurrency_used = await self._user_repository.get_keypair_concurrency_used(
            session_data.access_key
        )
        keypair_occupancy = await self._user_repository.get_keypair_occupancy(
            session_data.access_key
        )
        user_occupancy = await self._user_repository.get_user_occupancy(session_data.user_uuid)
        group_occupancy = await self._group_repository.get_group_occupancy(session_data.group_id)
        domain_occupancy = await self._domain_repository.get_domain_occupancy(
            session_data.domain_name
        )

        # Fetch additional data
        group_name = await self._group_repository.get_group_name(session_data.group_id)
        user_data = await self._user_repository.get_user_data(session_data.user_uuid)

        return ValidatorContext(
            session_data=session_data,
            session_starts_at=session_starts_at,
            session_dependencies=session_dependencies,
            pending_sessions=pending_sessions,
            keypair_resource_policy=keypair_resource_policy,
            user_main_keypair_resource_policy=user_main_keypair_resource_policy,
            group_resource_policy=group_resource_policy,
            domain_resource_policy=domain_resource_policy,
            keypair_concurrency_used=keypair_concurrency_used,
            keypair_occupancy=keypair_occupancy,
            user_occupancy=user_occupancy,
            group_occupancy=group_occupancy,
            domain_occupancy=domain_occupancy,
            group_name=group_name,
            user_data=user_data,
            known_slot_types=self._known_slot_types,
        )

    async def pick_session(
        self,
        pending_sessions: Sequence[SessionData],
        existing_sessions: Sequence[SessionData],
        total_capacity: ResourceSlot,
    ) -> Optional[SessionId]:
        """
        Pick a session to schedule using the configured policy.

        Args:
            pending_sessions: List of pending sessions for the scaling group
            existing_sessions: List of existing sessions for the scaling group
            total_capacity: Total available capacity in the scaling group

        Returns:
            The selected session ID, or None if no session can be picked
        """
        if not pending_sessions:
            return None

        # Apply any policy preprocessing
        await self._policy.apply()

        # Use policy to pick a session
        # Some policies (like DRF) need existing sessions and total capacity
        if hasattr(self._policy, "pick_session"):
            if (
                hasattr(self._policy.pick_session, "__code__")
                and self._policy.pick_session.__code__.co_argcount > 2
            ):
                # Policy expects existing_sessions and total_capacity (like DRF)
                session_id = self._policy.pick_session(
                    pending_sessions, existing_sessions, total_capacity
                )
            else:
                # Simple policy that only needs pending sessions
                session_id = self._policy.pick_session(pending_sessions)
            return session_id

        # Fallback to first session if policy doesn't implement pick_session
        return SessionId(pending_sessions[0].id)

    async def validate_session(
        self,
        session_data: SessionData,
    ) -> bool:
        """
        Validate if a session can be scheduled.

        Args:
            session_data: Session to validate

        Returns:
            True if all validations pass, False otherwise
        """
        # Create validator context for the session
        validator_context = await self._create_validator_context(session_data)

        # Run validators
        try:
            for validator in self._validators:
                await validator.validate(validator_context)
            return True
        except Exception:
            # Validation failed
            return False

    async def allocate_agent(
        self,
        agents: Sequence[AgentRow],
        session_data: SessionData,
    ) -> Optional[AgentId]:
        """
        Allocate an agent for the session using the configured allocator.

        Args:
            agents: List of available agents
            session_data: Session to allocate agent for

        Returns:
            Allocated agent ID, or None if no agent can be allocated
        """
        # Apply any allocator preprocessing
        await self._allocator.allocate()

        # Use allocator to select an agent
        # Different allocators have different parameter requirements
        if hasattr(self._allocator, "select_agent"):
            # For now, we don't have architecture info in SessionData
            # This would need to be fetched from the session's kernels
            # TODO: Add architecture info to SessionData or fetch from repository

            # Call select_agent with appropriate parameters
            return await self._allocator.select_agent(
                agents,
                session_data.requested_slots,
                requested_architecture=None,  # TODO: Get architecture from kernels
            )

        return None

    async def schedule(
        self,
        pending_sessions: Sequence[SessionData],
        existing_sessions: Sequence[SessionData],
        total_capacity: ResourceSlot,
        available_agents: Sequence[AgentRow],
    ) -> Optional[tuple[SessionId, AgentId]]:
        """
        Execute the full scheduling process: pick, validate, and allocate.

        Args:
            pending_sessions: List of pending sessions
            existing_sessions: List of existing sessions
            total_capacity: Total available capacity
            available_agents: List of available agents

        Returns:
            Tuple of (session_id, agent_id) if scheduling succeeds, None otherwise
        """
        # Pick a session
        session_id = await self.pick_session(pending_sessions, existing_sessions, total_capacity)
        if not session_id:
            return None

        # Find the selected session
        selected_session = None
        for session in pending_sessions:
            if SessionId(session.id) == session_id:
                selected_session = session
                break

        if not selected_session:
            return None

        # Validate the session
        if not await self.validate_session(selected_session):
            return None

        # Allocate an agent
        agent_id = await self.allocate_agent(available_agents, selected_session)
        if not agent_id:
            return None

        return (session_id, agent_id)
