"""Tests for ai.backend.common.dto.manager.v2.scheduling_history.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    RouteHistoryFilter,
    RouteHistoryOrder,
    SchedulingResultFilter,
    SearchDeploymentHistoryInput,
    SearchRouteHistoryInput,
    SearchSessionHistoryInput,
    SessionHistoryFilter,
    SessionHistoryOrder,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryOrderField,
    SchedulingResultType,
    SessionHistoryOrderField,
)


class TestSessionHistoryFilter:
    """Tests for SessionHistoryFilter model."""

    def test_default_creation_all_none(self) -> None:
        f = SessionHistoryFilter()
        assert f.session_id is None
        assert f.phase is None
        assert f.from_status is None
        assert f.to_status is None
        assert f.result is None
        assert f.error_code is None
        assert f.message is None

    def test_with_session_id_filter(self) -> None:
        session_id = uuid.uuid4()
        f = SessionHistoryFilter(session_id=UUIDFilter(equals=session_id))
        assert f.session_id is not None

    def test_with_result_filter(self) -> None:
        f = SessionHistoryFilter(
            result=SchedulingResultFilter(
                in_=[SchedulingResultType.SUCCESS, SchedulingResultType.FAILURE]
            )
        )
        assert f.result is not None
        assert f.result.in_ is not None
        assert len(f.result.in_) == 2
        assert SchedulingResultType.SUCCESS in f.result.in_

    def test_with_from_status_list(self) -> None:
        f = SessionHistoryFilter(from_status=["PENDING", "PREPARING"])
        assert f.from_status == ["PENDING", "PREPARING"]

    def test_with_phase_filter(self) -> None:
        f = SessionHistoryFilter(phase=StringFilter(equals="scheduling"))
        assert f.phase is not None


class TestSessionHistoryOrder:
    """Tests for SessionHistoryOrder model."""

    def test_default_direction_is_desc(self) -> None:
        order = SessionHistoryOrder(field=SessionHistoryOrderField.CREATED_AT)
        assert order.direction == OrderDirection.DESC

    def test_explicit_asc_direction(self) -> None:
        order = SessionHistoryOrder(
            field=SessionHistoryOrderField.UPDATED_AT, direction=OrderDirection.ASC
        )
        assert order.direction == OrderDirection.ASC

    def test_all_order_fields(self) -> None:
        for field in SessionHistoryOrderField:
            order = SessionHistoryOrder(field=field)
            assert order.field == field


class TestSearchSessionHistoryInput:
    """Tests for SearchSessionHistoryInput model."""

    def test_default_creation(self) -> None:
        req = SearchSessionHistoryInput()
        assert req.filter is None
        assert req.order is None
        assert req.limit == 50
        assert req.offset == 0

    def test_limit_minimum_valid(self) -> None:
        req = SearchSessionHistoryInput(limit=1)
        assert req.limit == 1

    def test_limit_maximum_valid(self) -> None:
        req = SearchSessionHistoryInput(limit=1000)
        assert req.limit == 1000

    def test_limit_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchSessionHistoryInput(limit=0)

    def test_limit_above_maximum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchSessionHistoryInput(limit=1001)

    def test_negative_offset_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchSessionHistoryInput(offset=-1)

    def test_with_filter_by_session_id(self) -> None:
        session_id = uuid.uuid4()
        f = SessionHistoryFilter(session_id=UUIDFilter(equals=session_id))
        req = SearchSessionHistoryInput(filter=f)
        assert req.filter is not None
        assert req.filter.session_id is not None

    def test_round_trip_serialization(self) -> None:
        req = SearchSessionHistoryInput(limit=25, offset=10)
        json_str = req.model_dump_json()
        restored = SearchSessionHistoryInput.model_validate_json(json_str)
        assert restored.limit == 25
        assert restored.offset == 10


class TestDeploymentHistoryFilter:
    """Tests for DeploymentHistoryFilter model."""

    def test_default_creation_all_none(self) -> None:
        f = DeploymentHistoryFilter()
        assert f.deployment_id is None
        assert f.phase is None
        assert f.result is None

    def test_with_deployment_id_filter(self) -> None:
        dep_id = uuid.uuid4()
        f = DeploymentHistoryFilter(deployment_id=UUIDFilter(equals=dep_id))
        assert f.deployment_id is not None

    def test_with_result_filter(self) -> None:
        f = DeploymentHistoryFilter(
            result=SchedulingResultFilter(equals=SchedulingResultType.STALE)
        )
        assert f.result is not None
        assert f.result.equals == SchedulingResultType.STALE


class TestDeploymentHistoryOrder:
    """Tests for DeploymentHistoryOrder model."""

    def test_default_direction_is_desc(self) -> None:
        order = DeploymentHistoryOrder(field=DeploymentHistoryOrderField.CREATED_AT)
        assert order.direction == OrderDirection.DESC

    def test_all_order_fields(self) -> None:
        for field in DeploymentHistoryOrderField:
            order = DeploymentHistoryOrder(field=field)
            assert order.field == field


class TestSearchDeploymentHistoryInput:
    """Tests for SearchDeploymentHistoryInput model."""

    def test_default_creation(self) -> None:
        req = SearchDeploymentHistoryInput()
        assert req.filter is None
        assert req.order is None
        assert req.limit == 50
        assert req.offset == 0

    def test_limit_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchDeploymentHistoryInput(limit=0)

    def test_round_trip_serialization(self) -> None:
        req = SearchDeploymentHistoryInput(limit=100, offset=0)
        json_str = req.model_dump_json()
        restored = SearchDeploymentHistoryInput.model_validate_json(json_str)
        assert restored.limit == 100


class TestRouteHistoryFilter:
    """Tests for RouteHistoryFilter model."""

    def test_default_creation_all_none(self) -> None:
        f = RouteHistoryFilter()
        assert f.route_id is None
        assert f.deployment_id is None
        assert f.result is None

    def test_with_route_id_filter(self) -> None:
        route_id = uuid.uuid4()
        f = RouteHistoryFilter(route_id=UUIDFilter(equals=route_id))
        assert f.route_id is not None

    def test_with_both_ids(self) -> None:
        route_id = uuid.uuid4()
        dep_id = uuid.uuid4()
        f = RouteHistoryFilter(
            route_id=UUIDFilter(equals=route_id),
            deployment_id=UUIDFilter(equals=dep_id),
        )
        assert f.route_id is not None
        assert f.deployment_id is not None


class TestRouteHistoryOrder:
    """Tests for RouteHistoryOrder model."""

    def test_default_direction_is_desc(self) -> None:
        order = RouteHistoryOrder(field=RouteHistoryOrderField.CREATED_AT)
        assert order.direction == OrderDirection.DESC

    def test_all_order_fields(self) -> None:
        for field in RouteHistoryOrderField:
            order = RouteHistoryOrder(field=field)
            assert order.field == field


class TestSearchRouteHistoryInput:
    """Tests for SearchRouteHistoryInput model."""

    def test_default_creation(self) -> None:
        req = SearchRouteHistoryInput()
        assert req.filter is None
        assert req.order is None
        assert req.limit == 50
        assert req.offset == 0

    def test_limit_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchRouteHistoryInput(limit=0)

    def test_round_trip_serialization(self) -> None:
        req = SearchRouteHistoryInput(limit=75, offset=25)
        json_str = req.model_dump_json()
        restored = SearchRouteHistoryInput.model_validate_json(json_str)
        assert restored.limit == 75
        assert restored.offset == 25
