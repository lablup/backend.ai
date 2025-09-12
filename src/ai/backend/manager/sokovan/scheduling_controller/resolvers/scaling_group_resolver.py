"""Resolver for determining the appropriate scaling group for a session."""

import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models import PRIVATE_SESSION_TYPES
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScalingGroupResolver:
    """Resolves the appropriate scaling group for session creation."""

    def resolve(
        self,
        spec: SessionCreationSpec,
        allowed_groups: list[AllowedScalingGroup],
    ) -> AllowedScalingGroup:
        """
        Resolve the scaling group name for the session.

        If a scaling group is specified in the spec, use it.
        Otherwise, auto-select based on session type and availability.

        Args:
            spec: Session creation specification
            allowed_groups: List of allowed scaling groups for the user

        Returns:
            str: The resolved scaling group name

        Raises:
            InvalidAPIParameters: If no accessible scaling group is available
        """
        # Auto-select scaling group based on session type
        public_sgroup_only = spec.session_type not in PRIVATE_SESSION_TYPES

        if public_sgroup_only:
            # For public session types, prefer public scaling groups
            for sg in allowed_groups:
                if not sg.is_private:
                    log.debug(f"Auto-selected public scaling group: {sg.name}")
                    return sg

        # Fall back to first allowed scaling group
        if allowed_groups:
            selected = allowed_groups[0]
            log.debug(f"Auto-selected first available scaling group: {selected.name}")
            return selected

        raise InvalidAPIParameters("No accessible scaling group available")
