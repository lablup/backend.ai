"""Tests for the user nested filter on keypair GQL filter types."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.keypair.request import (
    KeypairFilter as KeypairFilterDTO,
)
from ai.backend.manager.api.gql.base import UUIDFilter
from ai.backend.manager.api.gql.keypair.types.filters import (
    KeypairFilterGQL,
    KeypairUserNestedFilterGQL,
)


class TestKeypairUserNestedFilter:
    """Tests for KeypairUserNestedFilterGQL.to_pydantic()."""

    def test_to_pydantic_empty(self) -> None:
        nested = KeypairUserNestedFilterGQL()
        dto = nested.to_pydantic()
        assert dto.user_id is None

    def test_to_pydantic_user_id_equals(self) -> None:
        owner_id = uuid.uuid4()
        nested = KeypairUserNestedFilterGQL(user_id=UUIDFilter(equals=owner_id))
        dto = nested.to_pydantic()
        assert dto.user_id is not None
        assert dto.user_id.equals == owner_id

    def test_to_pydantic_user_id_in(self) -> None:
        owner_ids = [uuid.uuid4(), uuid.uuid4()]
        nested = KeypairUserNestedFilterGQL(user_id=UUIDFilter(in_=owner_ids))
        dto = nested.to_pydantic()
        assert dto.user_id is not None
        assert dto.user_id.in_ == owner_ids

    def test_filter_includes_user_nested(self) -> None:
        owner_id = uuid.uuid4()
        nested = KeypairUserNestedFilterGQL(user_id=UUIDFilter(equals=owner_id))
        filter_gql = KeypairFilterGQL(user=nested)
        dto = filter_gql.to_pydantic()
        assert isinstance(dto, KeypairFilterDTO)
        assert dto.user is not None
        assert dto.user.user_id is not None
        assert dto.user.user_id.equals == owner_id
