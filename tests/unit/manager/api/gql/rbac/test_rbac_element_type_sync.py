"""Sync guard: RBACElementTypeGQL must cover all RBACElementType members.

Prevents enum drift between the internal RBACElementType and its GraphQL
mirror from silently reaching production as a runtime ValueError.
"""

from __future__ import annotations

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.api.gql.rbac.types.permission import RBACElementTypeGQL


class TestRBACElementTypeEnumSync:
    def test_gql_enum_covers_all_internal_members(self) -> None:
        internal_values = {member.value for member in RBACElementType}
        gql_values = {member.value for member in RBACElementTypeGQL}
        missing = internal_values - gql_values
        assert not missing, (
            f"RBACElementTypeGQL is missing members present in RBACElementType: {missing}. "
            f"Add them to RBACElementTypeGQL to keep the enums in sync."
        )

    def test_from_element_roundtrip_for_all_members(self) -> None:
        for member in RBACElementType:
            gql_member = RBACElementTypeGQL.from_element(member)
            assert gql_member.value == member.value
            assert gql_member.to_element() == member
