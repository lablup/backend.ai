from __future__ import annotations

import uuid

from ai.backend.common.service_discovery.service_discovery import (
    ServiceEndpoint,
    ServiceMetadata,
)


def _manager_worker() -> ServiceMetadata:
    """What one worker registers. Its siblings share the listening socket."""
    return ServiceMetadata.for_endpoint(
        display_name="manager-i-core1",
        service_group="manager",
        version="26.9.0a4",
        endpoint=ServiceEndpoint(
            address="10.0.0.1",
            port=8081,
            protocol="http",
            prometheus_address="10.0.0.1:18080",
        ),
    )


def test_workers_of_one_endpoint_register_under_one_id() -> None:
    ids = {_manager_worker().id for _ in range(4)}

    assert len(ids) == 1


def test_the_id_survives_a_restart() -> None:
    """A restart re-registers the same endpoint, so it must land on the same entry.

    A fresh id would leave the old entry behind until the sweep clears it, and would
    start a new series for every metric carrying the id.
    """
    assert _manager_worker().id == _manager_worker().id


def test_a_different_endpoint_gets_a_different_id() -> None:
    other = ServiceMetadata.for_endpoint(
        display_name="manager-i-core2",
        service_group="manager",
        version="26.9.0a4",
        endpoint=ServiceEndpoint(
            address="10.0.0.2",
            port=8081,
            protocol="http",
            prometheus_address="10.0.0.2:18080",
        ),
    )

    assert other.id != _manager_worker().id


def test_two_groups_on_one_address_stay_distinct() -> None:
    agent = ServiceMetadata.for_endpoint(
        display_name="agent-cpu1",
        service_group="agent",
        version="26.9.0a4",
        endpoint=ServiceEndpoint(
            address="10.0.0.1",
            port=8081,
            protocol="http",
            prometheus_address="10.0.0.1:18080",
        ),
    )

    assert agent.id != _manager_worker().id


def test_labels_are_carried_through() -> None:
    meta = ServiceMetadata.for_endpoint(
        display_name="manager-i-core1",
        service_group="manager",
        version="26.9.0a4",
        endpoint=ServiceEndpoint(
            address="10.0.0.1",
            port=8081,
            protocol="http",
            prometheus_address="10.0.0.1:18080",
        ),
        labels={"stack": "latest"},
    )

    assert meta.labels == {"stack": "latest"}


def test_a_caller_that_owns_its_identity_still_passes_one() -> None:
    """Model service routes key their registry entry on the route id.

    The sweep there unregisters by that value, so it cannot be derived instead.
    """
    route_id = uuid.uuid4()

    meta = ServiceMetadata(
        id=route_id,
        display_name="route",
        service_group="model-service",
        version="1.0",
        endpoint=ServiceEndpoint(
            address="10.0.0.9",
            port=9000,
            protocol="http",
            prometheus_address="10.0.0.9:9000",
        ),
    )

    assert meta.id == route_id
