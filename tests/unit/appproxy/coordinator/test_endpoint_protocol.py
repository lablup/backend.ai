"""Tests for the per-endpoint ``protocol`` (``http`` default, ``tcp`` pass-through)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.common.types import ProxyProtocol
from ai.backend.appproxy.coordinator.models import Endpoint
from ai.backend.appproxy.coordinator.repositories.endpoint import EndpointRepository
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    CreateEndpointItem,
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)

_REPO_MODULE = "ai.backend.appproxy.coordinator.repositories.endpoint"


def _item(**extra: Any) -> CreateEndpointItem:
    return CreateEndpointItem(
        deployment_id=DeploymentID(uuid4()),
        service_name="svc",
        tags=TagsModel(
            session=SessionTagsModel(
                user_uuid=str(uuid4()), project_id=str(uuid4()), domain_name="d"
            ),
            endpoint=EndpointTagsModel(id=str(uuid4()), runtime_variant="custom"),
        ),
        **extra,
    )


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [({}, ProxyProtocol.HTTP), ({"protocol": "tcp"}, ProxyProtocol.TCP)],
)
async def test_new_circuit_gets_requested_protocol(
    kwargs: dict[str, Any], expected: ProxyProtocol
) -> None:
    repo = EndpointRepository(MagicMock())
    sess = MagicMock()
    sess.flush = AsyncMock()
    circuit = MagicMock()
    circuit.get_endpoint_url = AsyncMock(return_value="http://x")
    endpoints: dict[UUID, Endpoint] = {}

    with patch(f"{_REPO_MODULE}.add_circuit", AsyncMock(return_value=(circuit, MagicMock()))) as m:
        await repo._sync_one(sess, _item(**kwargs), endpoints, {})

    assert m.await_args is not None
    assert m.await_args.args[4] is expected
