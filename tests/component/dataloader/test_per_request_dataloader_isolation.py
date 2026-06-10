"""Component regression tests: GraphQL DataLoaders are scoped to one request.

Every ``/admin/gql/strawberry`` request must execute with its own ``DataLoaders``
instance, so a value cached by one request's loader is never served to a later
request. These tests exercise the caching behaviour itself through the real
stack — real Strawberry schema, real ImageAdapter/ImageService/ImageRepository,
and real DB rows: a change made to an image between two requests must be
visible to the second request.

With a process-wide shared DataLoaders instance, the second request is served
the first request's cached node without re-reading the DB, so both tests fail
deterministically.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.manager.models.image.row import ImageRow

_IMAGE_QUERY = "query($id: ID!) { imageV2(id: $id) { id identity { canonicalName } } }"


async def _query_image(
    registry: BackendAIClientRegistry,
    image_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Query imageV2 by id and return the (nullable) node payload."""
    result = await registry._client._request(
        "POST",
        "/admin/gql/strawberry",
        json={"query": _IMAGE_QUERY, "variables": {"id": str(image_id)}},
    )
    assert result is not None, "Expected a non-null JSON response from the GQL endpoint"
    resp = cast(dict[str, Any], result)
    assert not resp.get("errors"), f"Unexpected GQL errors: {resp.get('errors')}"
    return cast("dict[str, Any] | None", resp["data"]["imageV2"])


class TestPerRequestDataLoaderIsolation:
    async def test_update_between_requests_is_visible_to_the_next_request(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """Renaming an image between two requests must be visible to the second.

        A loader cache shared across requests would serve the first request's
        cached node, so the second response would still carry the old name.
        """
        image_id = image_fixture

        first = await _query_image(admin_registry, image_id)
        assert first is not None
        old_canonical = first["identity"]["canonicalName"]

        new_canonical = f"registry.test.local/testproject/renamed-{uuid.uuid4().hex[:8]}:latest"
        assert new_canonical != old_canonical
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.update(ImageRow.__table__)
                .where(ImageRow.__table__.c.id == image_id)
                .values(name=new_canonical)
            )

        second = await _query_image(admin_registry, image_id)
        assert second is not None
        assert second["identity"]["canonicalName"] == new_canonical

    async def test_deletion_between_requests_is_visible_to_the_next_request(
        self,
        admin_registry: BackendAIClientRegistry,
        image_fixture: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """Deleting an image between two requests must yield null on the second.

        A loader cache shared across requests would keep serving the deleted
        image's node from the first request's cache.
        """
        image_id = image_fixture

        assert await _query_image(admin_registry, image_id) is not None

        async with db_engine.begin() as conn:
            await conn.execute(
                ImageRow.__table__.delete().where(ImageRow.__table__.c.id == image_id)
            )

        assert await _query_image(admin_registry, image_id) is None
