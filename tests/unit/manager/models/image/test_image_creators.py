"""What an image records of the user it was committed for, and the scopes it joins."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.data.permission.global_entity import GlobalEntityIDCache, global_entity_id
from ai.backend.manager.models.image.creators import ImageCreator


@pytest.fixture
def public_scope_id() -> Iterator[GlobalEntityID]:
    GlobalEntityIDCache.fill({name: GlobalEntityID(uuid.uuid4()) for name in GlobalEntityName})
    try:
        yield global_entity_id(GlobalEntityName.PUBLIC)
    finally:
        GlobalEntityIDCache.clear()


def _creator(
    creator_id: UserID | None,
    *,
    customized: bool = False,
    registry_is_global: bool = False,
) -> ImageCreator:
    return ImageCreator(
        name="cr.test.io/stable/python:3.11",
        project="stable",
        architecture="x86_64",
        registry_id=ContainerRegistryID(uuid.uuid4()),
        registry="cr.test.io",
        image="python",
        tag="3.11",
        config_digest="sha256:abc",
        size_bytes=1,
        type=ImageType.COMPUTE,
        labels={"ai.backend.customized-image.owner": f"user:{creator_id}"},
        customized=customized,
        creator_id=creator_id,
        registry_is_global=registry_is_global,
    )


class TestImageCreator:
    def test_an_image_joins_the_registry_it_was_scanned_from(self) -> None:
        creator = _creator(None)

        assert tuple(creator.created_in(creator.build_row())) == (creator.registry_id,)

    def test_an_image_of_a_global_registry_joins_public_as_well(
        self, public_scope_id: GlobalEntityID
    ) -> None:
        creator = _creator(None, registry_is_global=True)

        assert set(creator.created_in(creator.build_row())) == {
            creator.registry_id,
            public_scope_id,
        }

    def test_a_customized_image_joins_what_every_other_image_joins(
        self, public_scope_id: GlobalEntityID
    ) -> None:
        """A session commit is the same kind of row in the same registry, so it joins no
        scope of its own."""
        creator = _creator(UserID(uuid.uuid4()), customized=True, registry_is_global=True)

        assert set(creator.created_in(creator.build_row())) == {
            creator.registry_id,
            public_scope_id,
        }

    def test_the_row_records_the_user_the_image_was_committed_for(self) -> None:
        user_id = UserID(uuid.uuid4())

        row = _creator(user_id, customized=True).build_row()

        assert (row.customized, row.creator_id) == (True, user_id)

    def test_an_image_that_is_not_customized_records_nobody(self) -> None:
        assert _creator(None).build_row().creator_id is None
