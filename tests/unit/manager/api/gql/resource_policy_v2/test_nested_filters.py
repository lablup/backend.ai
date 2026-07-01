"""Tests for the keypair nested filter on keypair resource policy GQL types."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    KeypairResourcePolicyFilter as KeypairResourcePolicyFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    ProjectResourcePolicyFilter as ProjectResourcePolicyFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    UserResourcePolicyFilter as UserResourcePolicyFilterDTO,
)
from ai.backend.manager.api.gql.base import StringFilter, UUIDFilter
from ai.backend.manager.api.gql.resource_policy_v2.types.filters import (
    KeypairResourcePolicyKeypairNestedFilterGQL,
    KeypairResourcePolicyV2Filter,
    ProjectResourcePolicyV2Filter,
    UserResourcePolicyV2Filter,
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


class TestKeypairResourcePolicyFilterCombinators:
    """Tests for AND/OR/NOT combinators on KeypairResourcePolicyV2Filter."""

    def test_to_pydantic_empty(self) -> None:
        dto = KeypairResourcePolicyV2Filter().to_pydantic()
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_to_pydantic_and(self) -> None:
        filter_gql = KeypairResourcePolicyV2Filter(
            AND=[
                KeypairResourcePolicyV2Filter(name=StringFilter(contains="gpu")),
                KeypairResourcePolicyV2Filter(name=StringFilter(contains="prod")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert isinstance(dto, KeypairResourcePolicyFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].name is not None
        assert dto.AND[0].name.contains == "gpu"

    def test_to_pydantic_or(self) -> None:
        filter_gql = KeypairResourcePolicyV2Filter(
            OR=[
                KeypairResourcePolicyV2Filter(name=StringFilter(contains="a")),
                KeypairResourcePolicyV2Filter(name=StringFilter(contains="b")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 2

    def test_to_pydantic_not(self) -> None:
        filter_gql = KeypairResourcePolicyV2Filter(
            NOT=[KeypairResourcePolicyV2Filter(name=StringFilter(equals="default"))]
        )
        dto = filter_gql.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "default"


class TestUserResourcePolicyFilterCombinators:
    """Tests for AND/OR/NOT combinators on UserResourcePolicyV2Filter."""

    def test_to_pydantic_empty(self) -> None:
        dto = UserResourcePolicyV2Filter().to_pydantic()
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_to_pydantic_and(self) -> None:
        filter_gql = UserResourcePolicyV2Filter(
            AND=[
                UserResourcePolicyV2Filter(name=StringFilter(contains="gpu")),
                UserResourcePolicyV2Filter(name=StringFilter(contains="prod")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert isinstance(dto, UserResourcePolicyFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_to_pydantic_or(self) -> None:
        filter_gql = UserResourcePolicyV2Filter(
            OR=[
                UserResourcePolicyV2Filter(name=StringFilter(contains="a")),
                UserResourcePolicyV2Filter(name=StringFilter(contains="b")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 2

    def test_to_pydantic_not(self) -> None:
        filter_gql = UserResourcePolicyV2Filter(
            NOT=[UserResourcePolicyV2Filter(name=StringFilter(equals="default"))]
        )
        dto = filter_gql.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1


class TestProjectResourcePolicyFilterCombinators:
    """Tests for AND/OR/NOT combinators on ProjectResourcePolicyV2Filter."""

    def test_to_pydantic_empty(self) -> None:
        dto = ProjectResourcePolicyV2Filter().to_pydantic()
        assert dto.AND is None
        assert dto.OR is None
        assert dto.NOT is None

    def test_to_pydantic_and(self) -> None:
        filter_gql = ProjectResourcePolicyV2Filter(
            AND=[
                ProjectResourcePolicyV2Filter(name=StringFilter(contains="gpu")),
                ProjectResourcePolicyV2Filter(name=StringFilter(contains="prod")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert isinstance(dto, ProjectResourcePolicyFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_to_pydantic_or(self) -> None:
        filter_gql = ProjectResourcePolicyV2Filter(
            OR=[
                ProjectResourcePolicyV2Filter(name=StringFilter(contains="a")),
                ProjectResourcePolicyV2Filter(name=StringFilter(contains="b")),
            ]
        )
        dto = filter_gql.to_pydantic()
        assert dto.OR is not None
        assert len(dto.OR) == 2

    def test_to_pydantic_not(self) -> None:
        filter_gql = ProjectResourcePolicyV2Filter(
            NOT=[ProjectResourcePolicyV2Filter(name=StringFilter(equals="default"))]
        )
        dto = filter_gql.to_pydantic()
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
