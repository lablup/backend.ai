"""Tests for the per-endpoint ``protocol`` (``http`` default, ``tcp`` pass-through)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from yarl import URL

from ai.backend.appproxy.common.types import AppMode, ProxyProtocol
from ai.backend.appproxy.coordinator.api.endpoint import (
    EndpointCreationRequestModel,
    _request_model_to_item,
)
from ai.backend.appproxy.coordinator.errors import EndpointProtocolMismatchError
from ai.backend.appproxy.coordinator.models import Endpoint
from ai.backend.appproxy.coordinator.repositories.endpoint import EndpointRepository
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.request import (
    BulkCreateEndpointRequest,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    CreateEndpointItem,
    EndpointTagsModel,
    RegisterRoutesItem,
    RouteEntry,
    SessionTagsModel,
    TagsModel,
    UpdateRoutesItem,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.types import EndpointProtocol

_REPO_MODULE = "ai.backend.appproxy.coordinator.repositories.endpoint"


def _tags() -> TagsModel:
    return TagsModel(
        session=SessionTagsModel(user_uuid=str(uuid4()), project_id=str(uuid4()), domain_name="d"),
        endpoint=EndpointTagsModel(id=str(uuid4()), runtime_variant="custom"),
    )


def _item(**extra: Any) -> CreateEndpointItem:
    return CreateEndpointItem(
        deployment_id=DeploymentID(uuid4()),
        service_name="svc",
        tags=_tags(),
        **extra,
    )


def _route_entry() -> RouteEntry:
    return RouteEntry(
        session_id=uuid4(), route_id=uuid4(), kernel_host="10.0.0.1", kernel_port=8000
    )


class TestProtocolDTO:
    def test_item_defaults_to_http(self) -> None:
        assert _item().protocol is EndpointProtocol.HTTP

    def test_item_accepts_tcp(self) -> None:
        assert _item(protocol="tcp").protocol is EndpointProtocol.TCP

    @pytest.mark.parametrize("value", ["grpc", "h2", "vnc", "TCP", ""])
    def test_item_rejects_other_values(self, value: str) -> None:
        with pytest.raises(ValidationError):
            _item(protocol=value)

    def test_bulk_request_carries_protocol(self) -> None:
        request = BulkCreateEndpointRequest.model_validate({
            "endpoints": [_item(protocol="tcp").model_dump(mode="json", by_alias=True)]
        })
        assert request.endpoints[0].protocol is EndpointProtocol.TCP

    @pytest.mark.parametrize(
        ("extra", "expected"),
        [({}, EndpointProtocol.HTTP), ({"protocol": "tcp"}, EndpointProtocol.TCP)],
    )
    def test_single_endpoint_model_maps_to_item(
        self, extra: dict[str, Any], expected: EndpointProtocol
    ) -> None:
        params = EndpointCreationRequestModel.model_validate({
            "version": "v2",
            "service_name": "svc",
            "tags": {
                "session": {
                    "user_uuid": str(uuid4()),
                    "group_id": str(uuid4()),
                    "domain_name": "d",
                },
                "endpoint": {"id": str(uuid4()), "runtime_variant": "custom", "existing_url": None},
            },
            **extra,
        })
        # ``_request_model_to_item`` re-validates the dumped tags into the common DTO,
        # which wants string ids; hand it a stand-in so this test only covers protocol.
        tags = MagicMock()
        tags.session.model_dump.return_value = {
            "user_uuid": str(uuid4()),
            "project_id": str(uuid4()),
            "domain_name": "d",
        }
        tags.endpoint.model_dump.return_value = {"id": str(uuid4()), "runtime_variant": "custom"}
        params = params.model_copy(update={"tags": tags})
        assert _request_model_to_item(DeploymentID(uuid4()), params).protocol == expected

    def test_single_endpoint_model_rejects_unknown_protocol(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            EndpointCreationRequestModel.model_validate({
                "version": "v2",
                "service_name": "svc",
                "tags": {
                    "session": {
                        "user_uuid": str(uuid4()),
                        "group_id": str(uuid4()),
                        "domain_name": "d",
                    },
                    "endpoint": {
                        "id": str(uuid4()),
                        "runtime_variant": "custom",
                        "existing_url": None,
                    },
                },
                "protocol": "grpc",
            })


class TestEndpointRow:
    def test_create_defaults_to_http(self) -> None:
        endpoint = Endpoint.create(uuid4())
        assert endpoint.protocol is ProxyProtocol.HTTP

    def test_create_stores_tcp(self) -> None:
        endpoint = Endpoint.create(uuid4(), protocol=ProxyProtocol.TCP)
        assert endpoint.protocol is ProxyProtocol.TCP


class TestSyncOneProtocol:
    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [({}, ProxyProtocol.HTTP), ({"protocol": "tcp"}, ProxyProtocol.TCP)],
    )
    async def test_add_circuit_gets_endpoint_protocol(
        self, kwargs: dict[str, Any], expected: ProxyProtocol
    ) -> None:
        repo = EndpointRepository(MagicMock())
        sess = MagicMock()
        sess.flush = AsyncMock()
        circuit = MagicMock()
        circuit.get_endpoint_url = AsyncMock(return_value="http://x")
        item = _item(**kwargs)
        endpoints: dict[UUID, Endpoint] = {}  # DeploymentID is a UUID NewType

        with patch(
            f"{_REPO_MODULE}.add_circuit", AsyncMock(return_value=(circuit, MagicMock()))
        ) as m:
            await repo._sync_one(sess, item, endpoints, {})

        assert m.await_args is not None
        assert m.await_args.args[4] is expected
        assert m.await_args.args[5] is AppMode.INFERENCE
        assert endpoints[item.deployment_id].protocol is expected

    async def test_existing_endpoint_row_without_circuit_follows_request(self) -> None:
        repo = EndpointRepository(MagicMock())
        sess = MagicMock()
        sess.flush = AsyncMock()
        circuit = MagicMock()
        circuit.get_endpoint_url = AsyncMock(return_value="http://x")
        item = _item(protocol="tcp")
        endpoints: dict[UUID, Endpoint] = {item.deployment_id: Endpoint.create(item.deployment_id)}

        with patch(
            f"{_REPO_MODULE}.add_circuit", AsyncMock(return_value=(circuit, MagicMock()))
        ) as m:
            await repo._sync_one(sess, item, endpoints, {})

        assert m.await_args is not None
        assert m.await_args.args[4] is ProxyProtocol.TCP

    async def test_existing_circuit_protocol_mismatch_fails_item(self) -> None:
        repo = EndpointRepository(MagicMock())
        item = _item(protocol="tcp")
        endpoint = Endpoint.create(item.deployment_id)
        circuit = MagicMock()
        circuit.protocol = ProxyProtocol.HTTP

        with pytest.raises(EndpointProtocolMismatchError) as exc_info:
            await repo._sync_one(
                MagicMock(), item, {item.deployment_id: endpoint}, {item.deployment_id: circuit}
            )

        assert exc_info.value.status_code == 409
        assert endpoint.protocol is ProxyProtocol.HTTP

    async def test_existing_circuit_same_protocol_is_idempotent(self) -> None:
        repo = EndpointRepository(MagicMock())
        item = _item(protocol="tcp")
        endpoint = Endpoint.create(item.deployment_id, protocol=ProxyProtocol.TCP)
        circuit = MagicMock()
        circuit.protocol = ProxyProtocol.TCP
        circuit.get_endpoint_url = AsyncMock(return_value="http://x")

        synced = await repo._sync_one(
            MagicMock(), item, {item.deployment_id: endpoint}, {item.deployment_id: circuit}
        )

        assert synced.new_circuit is None


class TestExistingUrlWorkerMatchProtocol:
    @pytest.mark.parametrize("protocol", [ProxyProtocol.HTTP, ProxyProtocol.TCP])
    async def test_both_queries_filter_by_protocol(self, protocol: ProxyProtocol) -> None:
        repo = EndpointRepository(MagicMock())
        statements: list[Any] = []

        async def _execute(stmt: Any) -> MagicMock:
            statements.append(stmt)
            result = MagicMock()
            result.scalar.return_value = None
            result.scalars.return_value.all.return_value = []
            return result

        sess = MagicMock()
        sess.execute = AsyncMock(side_effect=_execute)

        matched = await repo._match_worker_for_existing_url(
            sess, URL("http://svc.example.com:10205"), protocol
        )

        assert matched == (None, None, None)
        assert len(statements) == 2
        for stmt in statements:
            assert protocol in stmt.compile().params.values()
            assert "workers.protocol" in str(stmt)


def _repo_with_circuit(circuit: MagicMock) -> EndpointRepository:
    repo = EndpointRepository(MagicMock())

    @asynccontextmanager
    async def _session() -> AsyncIterator[MagicMock]:
        sess = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = [circuit]
        sess.scalars = AsyncMock(return_value=scalars)
        yield sess

    cast(Any, repo)._begin_session_read_committed = _session
    return repo


def _circuit_for(deployment_id: DeploymentID, protocol: ProxyProtocol) -> MagicMock:
    circuit = MagicMock()
    circuit.endpoint_id = UUID(str(deployment_id))
    circuit.route_info = []
    circuit.protocol = protocol
    return circuit


class TestRouteInfoProtocol:
    @pytest.mark.parametrize(
        "expected",
        [ProxyProtocol.HTTP, ProxyProtocol.TCP],
    )
    async def test_update_routes(self, expected: ProxyProtocol) -> None:
        dep = DeploymentID(uuid4())
        circuit = _circuit_for(dep, expected)
        repo = _repo_with_circuit(circuit)

        results = await repo.update_routes([
            UpdateRoutesItem(deployment_id=dep, routes=[_route_entry()])
        ])

        assert results[0].success
        assert [r.protocol for r in circuit.route_info] == [expected]

    @pytest.mark.parametrize(
        "expected",
        [ProxyProtocol.HTTP, ProxyProtocol.TCP],
    )
    async def test_register_routes(self, expected: ProxyProtocol) -> None:
        dep = DeploymentID(uuid4())
        circuit = _circuit_for(dep, expected)
        repo = _repo_with_circuit(circuit)

        results = await repo.register_routes([
            RegisterRoutesItem(deployment_id=dep, routes=[_route_entry()])
        ])

        assert results[0].success
        assert [r.protocol for r in circuit.route_info] == [expected]
