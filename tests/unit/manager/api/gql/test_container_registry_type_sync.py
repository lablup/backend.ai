"""Sync guard: ContainerRegistryTypeGQL must cover all ContainerRegistryType members.

Prevents enum drift between the internal ContainerRegistryType and its GraphQL
mirror from silently reaching production as a runtime ValueError.
"""

from __future__ import annotations

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.api.gql.container_registry.types import ContainerRegistryTypeGQL


class TestContainerRegistryTypeEnumSync:
    def test_gql_enum_covers_all_internal_members(self) -> None:
        internal_values = {member.value for member in ContainerRegistryType}
        gql_values = {member.value for member in ContainerRegistryTypeGQL}
        missing = internal_values - gql_values
        assert not missing, (
            f"ContainerRegistryTypeGQL is missing members present in ContainerRegistryType: {missing}. "
            f"Add them to ContainerRegistryTypeGQL to keep the enums in sync."
        )

    def test_value_based_conversion_for_all_members(self) -> None:
        for member in ContainerRegistryType:
            gql_member = ContainerRegistryTypeGQL(member.value)
            assert gql_member.value == member.value
