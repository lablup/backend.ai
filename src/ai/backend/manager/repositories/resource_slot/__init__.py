"""Resource Slot repository package."""

from .repositories import ResourceSlotRepositories
from .repository import ResourceSlotRepository
from .upserters import AgentResourceUpserterSpec

__all__ = (
    # Repositories
    "ResourceSlotRepositories",
    "ResourceSlotRepository",
    # Upserter specs
    "AgentResourceUpserterSpec",
)
