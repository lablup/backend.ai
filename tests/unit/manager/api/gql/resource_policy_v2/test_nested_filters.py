"""Tests for the keypair nested filter on keypair resource policy GQL types."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    KeypairResourcePolicyFilter as KeypairResourcePolicyFilterDTO,
)
from ai.backend.manager.api.gql.base import UUIDFilter
from ai.backend.manager.api.gql.resource_policy_v2.types.filters import (
    KeypairResourcePolicyKeypairNestedFilterGQL,
    KeypairResourcePolicyV2Filter,
)


class TestKeypairResourcePolicyKeypairNestedFilter:
    """Tests for KeypairResourcePolicyKeypairNestedFilterGQL.to_pydantic()."""

    def test_to_pydantic_empty(self) -> None:
        nested = KeypairResourcePolicyKeypairNestedFilterGQL()
        dto = nested.to_pydantic()
        assert dto.user_id is None

    def test_to_pydantic_user_id_equals(self) -> None:
        owner_id = uuid.uuid4()
        nested = KeypairResourcePolicyKeypairNestedFilterGQL(user_id=UUIDFilter(equals=owner_id))
        dto = nested.to_pydantic()
        assert dto.user_id is not None
        assert dto.user_id.equals == owner_id

    def test_to_pydantic_user_id_in(self) -> None:
        owner_ids = [uuid.uuid4(), uuid.uuid4()]
        nested = KeypairResourcePolicyKeypairNestedFilterGQL(user_id=UUIDFilter(in_=owner_ids))
        dto = nested.to_pydantic()
        assert dto.user_id is not None
        assert dto.user_id.in_ == owner_ids

    def test_filter_includes_keypair_nested(self) -> None:
        owner_id = uuid.uuid4()
        nested = KeypairResourcePolicyKeypairNestedFilterGQL(user_id=UUIDFilter(equals=owner_id))
        filter_gql = KeypairResourcePolicyV2Filter(keypair=nested)
        dto = filter_gql.to_pydantic()
        assert isinstance(dto, KeypairResourcePolicyFilterDTO)
        assert dto.keypair is not None
        assert dto.keypair.user_id is not None
        assert dto.keypair.user_id.equals == owner_id
