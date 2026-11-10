from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType

__all__ = (
    "DomainUsageBucketFieldType",
    "ProjectUsageBucketFieldType",
    "UserUsageBucketFieldType",
)


# A bucket is one scope's usage in one resource group over one window, so neither side
# alone owns the row and the wiring fixes no entity type for it.
class DomainUsageBucketFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "domain_usage_bucket"

    @override
    @classmethod
    def description(cls) -> str:
        return "One period's resource usage of a domain."


class ProjectUsageBucketFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "project_usage_bucket"

    @override
    @classmethod
    def description(cls) -> str:
        return "One period's resource usage of a project."


class UserUsageBucketFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "user_usage_bucket"

    @override
    @classmethod
    def description(cls) -> str:
        return "One period's resource usage of a user."
