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
        return "A domain's scheduling priority in a resource group, from past usage and weight."


class ProjectFairShareEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "project_fair_share"

    @override
    @classmethod
    def description(cls) -> str:
        return "A project's scheduling priority in a resource group, from past usage and weight."


class UserFairShareEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "user_fair_share"

    @override
    @classmethod
    def description(cls) -> str:
        return "A user's scheduling priority in a resource group, from past usage and weight."
