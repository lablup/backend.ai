"""Entity types of the fair share tables."""

from typing import override

from ai.backend.common.data.entity.types import EntityType

__all__ = (
    "DomainFairShareEntityType",
    "ProjectFairShareEntityType",
    "UserFairShareEntityType",
)


class DomainFairShareEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "domain_fair_share"

    @override
    @classmethod
    def description(cls) -> str:
        return "A domain's fair-share weight in a resource group."


class ProjectFairShareEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "project_fair_share"

    @override
    @classmethod
    def description(cls) -> str:
        return "A project's fair-share weight in a resource group."


class UserFairShareEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "user_fair_share"

    @override
    @classmethod
    def description(cls) -> str:
        return "A user's fair-share weight in a resource group."
