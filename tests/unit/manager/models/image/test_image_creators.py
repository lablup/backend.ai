"""What an image records of the user it was committed for, and the scopes it joins."""

from __future__ import annotations

import uuid

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.image.creators import ImageCreator


def _creator(creator_id: UserID | None, created_in_project_id: ProjectID | None) -> ImageCreator:
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
        creator_id=creator_id,
        created_in_project_id=created_in_project_id,
    )


class TestImageCreator:
    def test_a_customized_image_joins_the_project_it_is_created_in(self) -> None:
        project_id = ProjectID(uuid.uuid4())
        creator = _creator(UserID(uuid.uuid4()), project_id)

        assert set(creator.created_in(creator.build_row())) == {
            creator.registry_id,
            project_id,
        }

    def test_an_image_without_a_project_joins_the_registry_alone(self) -> None:
        creator = _creator(None, None)

        assert tuple(creator.created_in(creator.build_row())) == (creator.registry_id,)

    def test_the_row_records_the_user_the_image_was_committed_for(self) -> None:
        user_id = UserID(uuid.uuid4())

        assert _creator(user_id, ProjectID(uuid.uuid4())).build_row().creator_id == user_id

    def test_an_image_that_is_not_customized_records_nobody(self) -> None:
        assert _creator(None, None).build_row().creator_id is None
