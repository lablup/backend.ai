"""purge_image_by_id keeps the image row until the registry artifact is removed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from graphql_relay import to_global_id

from ai.backend.common.exception import ErrorDomain, ErrorOperation, PassthroughError
from ai.backend.manager.api.gql_legacy.image import PurgeImageById, PurgeImageOptions


class TestPurgeImageById:
    @pytest.fixture
    def info_of_a_request_whose_untag_fails(self) -> MagicMock:
        info = MagicMock()
        image_processors = info.context.processors.image
        image_processors.purge_image_by_id.run = AsyncMock()
        image_processors.untag_image_from_registry.run = AsyncMock(
            side_effect=PassthroughError.from_http_status(
                503,
                domain=ErrorDomain.CONTAINER_REGISTRY,
                operation=ErrorOperation.HARD_DELETE,
            )
        )
        return info

    async def test_the_image_is_not_purged_when_the_untag_fails(
        self, info_of_a_request_whose_untag_fails: MagicMock
    ) -> None:
        with pytest.raises(PassthroughError):
            await PurgeImageById.mutate(
                None,
                info_of_a_request_whose_untag_fails,
                to_global_id("ImageNode", str(uuid4())),
                PurgeImageOptions(remove_from_registry=True),
            )

        info_of_a_request_whose_untag_fails.context.processors.image.purge_image_by_id.run.assert_not_called()
