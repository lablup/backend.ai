"""Tests for the keypair GQL filter types."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.keypair.request import (
    KeypairFilter as KeypairFilterDTO,
)
from ai.backend.manager.api.gql.base import UUIDFilter
from ai.backend.manager.api.gql.keypair.types.filters import KeypairFilterGQL


class TestKeypairUserIdFilter:
    """Tests for the flat ``user_id`` owner filter on KeypairFilterGQL."""

    def test_to_pydantic_empty(self) -> None:
        dto = KeypairFilterGQL().to_pydantic()
        assert isinstance(dto, KeypairFilterDTO)
        assert dto.user_id is None

    def test_to_pydantic_user_id_equals(self) -> None:
        owner_id = uuid.uuid4()
        dto = KeypairFilterGQL(user_id=UUIDFilter(equals=owner_id)).to_pydantic()
        assert isinstance(dto, KeypairFilterDTO)
        assert dto.user_id is not None
        assert dto.user_id.equals == owner_id

    def test_to_pydantic_user_id_in(self) -> None:
        owner_ids = [uuid.uuid4(), uuid.uuid4()]
        dto = KeypairFilterGQL(user_id=UUIDFilter(in_=owner_ids)).to_pydantic()
        assert isinstance(dto, KeypairFilterDTO)
        assert dto.user_id is not None
        assert dto.user_id.in_ == owner_ids
