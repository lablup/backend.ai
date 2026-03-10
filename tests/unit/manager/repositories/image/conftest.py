"""
Conftest for image repository tests.

These imports register SQLAlchemy ORM mappers that KernelRow
(imported transitively via ImageConditions -> options.py) depends on
through its relationship() definitions.
"""

from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.session.row import SessionRow

__all__ = ["AgentRow", "GroupRow", "SessionRow"]
