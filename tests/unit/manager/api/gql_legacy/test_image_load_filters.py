"""What each image load filter admits, now that the creator column answers it."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.docker import LabelName
from ai.backend.manager.api.gql_legacy.image import Image
from ai.backend.manager.data.image.types import KVPair
from ai.backend.manager.models.image import ImageLoadFilter
from ai.backend.manager.models.user import UserRole

ME = UserID(uuid.uuid4())
SOMEBODY_ELSE = UserID(uuid.uuid4())


def _ctx(user_role: UserRole) -> Any:
    ctx = MagicMock()
    ctx.user = {"role": user_role, "uuid": ME}
    return ctx


def _image(creator_id: UserID | None, *, operational: bool = False) -> Image:
    item = Image(
        id=uuid.uuid4(),
        name="cr.test.io/stable/python:3.11",
        labels=[KVPair(key=LabelName.FEATURES.value, value="operation")] if operational else [],
    )
    item.creator_id = creator_id
    return item


class TestMatchesFilter:
    def test_general_filter_admits_an_image_that_is_not_customized(self) -> None:
        item = _image(None)

        assert item.matches_filter(_ctx(UserRole.USER), {ImageLoadFilter.GENERAL})

    def test_general_filter_rejects_a_customized_image(self) -> None:
        item = _image(ME)

        assert not item.matches_filter(_ctx(UserRole.USER), {ImageLoadFilter.GENERAL})

    def test_customized_filter_admits_what_was_committed_for_the_caller(self) -> None:
        item = _image(ME)

        assert item.matches_filter(_ctx(UserRole.USER), {ImageLoadFilter.CUSTOMIZED})

    def test_customized_filter_rejects_what_was_committed_for_somebody_else(self) -> None:
        item = _image(SOMEBODY_ELSE)

        assert not item.matches_filter(_ctx(UserRole.USER), {ImageLoadFilter.CUSTOMIZED})

    @pytest.mark.parametrize(
        ("user_role", "admitted"),
        [(UserRole.SUPERADMIN, True), (UserRole.ADMIN, False), (UserRole.USER, False)],
    )
    def test_customized_global_filter_is_the_superadmin_view(
        self, user_role: UserRole, admitted: bool
    ) -> None:
        item = _image(SOMEBODY_ELSE)

        assert item.matches_filter(_ctx(user_role), {ImageLoadFilter.CUSTOMIZED_GLOBAL}) is admitted

    def test_operational_label_still_decides_on_its_own(self) -> None:
        item = _image(None, operational=True)
        ctx = _ctx(UserRole.USER)

        assert item.matches_filter(ctx, {ImageLoadFilter.OPERATIONAL})
        assert not item.matches_filter(ctx, {ImageLoadFilter.GENERAL})
