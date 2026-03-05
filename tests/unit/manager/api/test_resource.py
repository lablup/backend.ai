"""
Tests for resource.py API handlers.

Tests the new-style ResourceHandler (constructor DI) directly.

Legacy wrapper handlers (list_presets, check_presets, recalculate_usage,
usage_per_month, usage_per_period, user_month_stats, admin_month_stats,
get_watcher_status, watcher_agent_start, watcher_agent_stop,
watcher_agent_restart) have been removed along with their create_app()
shim.  Only get_container_registries remains as a backward-compatible
re-export used by rest/etcd/handler.py.
"""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.api_handlers import BodyParam, QueryParam
from ai.backend.common.dto.manager.resource.request import (
    CheckPresetsRequest,
    UsagePerPeriodQuery,
    WatcherAgentRequest,
)
from ai.backend.common.types import LegacyResourceSlotState as ResourceSlotState
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.rest.resource.handler import ResourceHandler
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.models.user import UserRole

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_root_ctx() -> MagicMock:
    """RootContext mock with processors."""
    root_ctx = MagicMock()
    root_ctx.config_provider.legacy_etcd_config_loader.get_manager_status = AsyncMock(
        return_value=ManagerStatus.RUNNING
    )
    return root_ctx


@pytest.fixture
def mock_processors() -> MagicMock:
    """Mock Processors for ResourceHandler constructor injection."""
    return MagicMock()


@pytest.fixture
def handler(mock_processors: MagicMock) -> ResourceHandler:
    """ResourceHandler instance with mock processors."""
    return ResourceHandler(
        resource_preset=mock_processors.resource_preset,
        agent=mock_processors.agent,
        group=mock_processors.group,
        user=mock_processors.user,
        container_registry=mock_processors.container_registry,
    )


@pytest.fixture
def superadmin_context() -> UserContext:
    """UserContext for superadmin endpoints."""
    return UserContext(
        user_uuid=uuid.uuid4(),
        user_email="admin@example.com",
        user_domain="default",
        user_role=UserRole.SUPERADMIN,
        access_key="AKTEST",
        is_admin=True,
        is_superadmin=True,
    )


@pytest.fixture
def unauthorized_request(mock_root_ctx: MagicMock) -> MagicMock:
    """Mock request for unauthorized user."""
    req = MagicMock(spec=web.Request)
    req.app = {"_root.context": mock_root_ctx}
    req.get = lambda k, default=None: {
        "is_authorized": False,
        "is_superadmin": False,
    }.get(k, default)
    return req


@pytest.fixture
def authorized_request(mock_root_ctx: MagicMock) -> MagicMock:
    """Mock request for authorized (non-admin) user."""
    req = MagicMock(spec=web.Request)
    req.app = {"_root.context": mock_root_ctx}
    req.get = lambda k, default=None: {
        "is_authorized": True,
        "is_superadmin": False,
    }.get(k, default)
    # Enable dict-like access for request["keypair"], request["user"]
    storage: dict[str, Any] = {
        "user": {"uuid": uuid.uuid4(), "email": "test@example.com", "domain_name": "default"},
        "keypair": {"access_key": "AKTEST"},
        "is_admin": False,
        "is_superadmin": False,
    }
    req.__getitem__ = lambda _, key: storage[key]
    req.__setitem__ = lambda _, key, value: storage.__setitem__(key, value)
    return req


@pytest.fixture
def superadmin_request(mock_root_ctx: MagicMock) -> MagicMock:
    """Mock request for superadmin user."""
    req = MagicMock(spec=web.Request)
    req.app = {"_root.context": mock_root_ctx}
    storage: dict[str, Any] = {
        "user": {"uuid": uuid.uuid4(), "email": "admin@example.com", "domain_name": "default"},
        "keypair": {"access_key": "AKTEST"},
        "is_admin": True,
        "is_superadmin": True,
    }
    req.__getitem__ = lambda _, key: storage[key]
    req.__setitem__ = lambda _, key, value: storage.__setitem__(key, value)
    req.get = lambda k, default=None: {
        "is_authorized": True,
        "is_superadmin": True,
    }.get(k, default)
    return req


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestWatcherAgentStart:
    """Tests for watcher_agent_start handler (new-style)."""

    async def test_calls_processor_with_agent_id_and_returns_data(
        self,
        handler: ResourceHandler,
        mock_processors: MagicMock,
        superadmin_context: UserContext,
    ) -> None:
        """Verify agent_id is passed to Action and data is returned."""
        body: BodyParam[WatcherAgentRequest] = BodyParam(WatcherAgentRequest)
        body.from_body({"agent_id": "agent-001"})
        expected_data = {"started": True}
        mock_result = MagicMock()
        mock_result.data = expected_data
        mock_processors.agent.watcher_agent_start.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await handler.watcher_agent_start(body, superadmin_context)

        call_args = mock_processors.agent.watcher_agent_start.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.agent_id == "agent-001"
        assert response.status_code == HTTPStatus.OK
        assert response.to_json == expected_data


class TestWatcherAgentStop:
    """Tests for watcher_agent_stop handler (new-style)."""

    async def test_calls_processor_with_agent_id_and_returns_data(
        self,
        handler: ResourceHandler,
        mock_processors: MagicMock,
        superadmin_context: UserContext,
    ) -> None:
        """Verify agent_id is passed to Action and data is returned."""
        body: BodyParam[WatcherAgentRequest] = BodyParam(WatcherAgentRequest)
        body.from_body({"agent_id": "agent-001"})
        expected_data = {"stopped": True}
        mock_result = MagicMock()
        mock_result.data = expected_data
        mock_processors.agent.watcher_agent_stop.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await handler.watcher_agent_stop(body, superadmin_context)

        call_args = mock_processors.agent.watcher_agent_stop.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.agent_id == "agent-001"
        assert response.status_code == HTTPStatus.OK
        assert response.to_json == expected_data


class TestWatcherAgentRestart:
    """Tests for watcher_agent_restart handler (new-style)."""

    async def test_calls_processor_with_agent_id_and_returns_data(
        self,
        handler: ResourceHandler,
        mock_processors: MagicMock,
        superadmin_context: UserContext,
    ) -> None:
        """Verify agent_id is passed to Action and data is returned."""
        body: BodyParam[WatcherAgentRequest] = BodyParam(WatcherAgentRequest)
        body.from_body({"agent_id": "agent-001"})
        expected_data = {"restarted": True}
        mock_result = MagicMock()
        mock_result.data = expected_data
        mock_processors.agent.watcher_agent_restart.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await handler.watcher_agent_restart(body, superadmin_context)

        call_args = mock_processors.agent.watcher_agent_restart.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.agent_id == "agent-001"
        assert response.status_code == HTTPStatus.OK
        assert response.to_json == expected_data


class TestUsagePerPeriod:
    """Tests for usage_per_period handler (new-style)."""

    async def test_project_id_default_is_none(
        self,
        handler: ResourceHandler,
        mock_processors: MagicMock,
        superadmin_context: UserContext,
    ) -> None:
        """Verify project_id defaults to None."""
        query: QueryParam[UsagePerPeriodQuery] = QueryParam(UsagePerPeriodQuery)
        query.from_query({
            "start_date": "20240101",
            "end_date": "20240131",
        })
        mock_result = MagicMock()
        mock_result.result = []
        mock_processors.group.usage_per_period.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        await handler.usage_per_period(query, superadmin_context)

        call_args = mock_processors.group.usage_per_period.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.project_id is None


class TestCheckPresets:
    """Tests for check_presets handler (new-style)."""

    def _create_mock_result(self) -> tuple[MagicMock, list[SlotQuantity]]:
        """Create a mock CheckResourcePresetsResult with SlotQuantity list."""
        slot_quantities = [
            SlotQuantity(slot_name="cpu", quantity=Decimal("1")),
            SlotQuantity(slot_name="mem", quantity=Decimal("1073741824")),
        ]
        mock_result = MagicMock()
        mock_result.presets = [{"name": "small"}]
        mock_result.keypair_limits = slot_quantities
        mock_result.keypair_using = slot_quantities
        mock_result.keypair_remaining = slot_quantities
        mock_result.group_limits = slot_quantities
        mock_result.group_using = slot_quantities
        mock_result.group_remaining = slot_quantities
        mock_result.scaling_group_remaining = slot_quantities
        mock_result.scaling_groups = {
            "sg-test": {
                ResourceSlotState.OCCUPIED: slot_quantities,
                ResourceSlotState.AVAILABLE: slot_quantities,
            }
        }
        return mock_result, slot_quantities

    async def test_passes_params_to_action_and_returns_response(
        self,
        handler: ResourceHandler,
        mock_processors: MagicMock,
    ) -> None:
        """Verify group, scaling_group, access_key etc. are passed to Action and response is returned."""
        user_uuid = uuid.uuid4()
        body: BodyParam[CheckPresetsRequest] = BodyParam(CheckPresetsRequest)
        body.from_body({"scaling_group": "sg-test", "group": "test-group"})
        user_context = UserContext(
            user_uuid=user_uuid,
            user_email="test@example.com",
            user_domain="default",
            user_role=UserRole.USER,
            access_key="AKTEST",
            is_admin=False,
            is_superadmin=False,
        )
        mock_req = MagicMock(spec=web.Request)
        storage: dict[str, Any] = {
            "keypair": {"access_key": "AKTEST", "resource_policy": "default"},
        }
        mock_req.__getitem__ = lambda _, key: storage[key]
        req_ctx = RequestCtx(request=mock_req)
        mock_result, _ = self._create_mock_result()
        mock_processors.resource_preset.check_presets.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await handler.check_presets(body, user_context, req_ctx)

        call_args = mock_processors.resource_preset.check_presets.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.access_key == "AKTEST"
        assert action.resource_policy == "default"
        assert action.domain_name == "default"
        assert action.user_id == user_uuid
        assert action.group == "test-group"
        assert action.scaling_group == "sg-test"
        assert response.status_code == HTTPStatus.OK
        response_body = response.to_json
        assert response_body is not None
        assert isinstance(response_body, dict)
        assert response_body["presets"] == [{"name": "small"}]
        expected_json = '{"cpu": "1", "mem": "1073741824"}'
        assert response_body["keypair_limits"] == expected_json
        assert response_body["keypair_using"] == expected_json
        assert response_body["keypair_remaining"] == expected_json
        assert response_body["group_limits"] == expected_json
        assert response_body["group_using"] == expected_json
        assert response_body["group_remaining"] == expected_json
        assert response_body["scaling_group_remaining"] == expected_json

    async def test_converts_resource_slots_to_json(
        self,
        handler: ResourceHandler,
        mock_processors: MagicMock,
    ) -> None:
        """Verify list[SlotQuantity] is converted to JSON string in response."""
        user_uuid = uuid.uuid4()
        body: BodyParam[CheckPresetsRequest] = BodyParam(CheckPresetsRequest)
        body.from_body({"scaling_group": "sg-test", "group": "default"})
        user_context = UserContext(
            user_uuid=user_uuid,
            user_email="test@example.com",
            user_domain="default",
            user_role=UserRole.USER,
            access_key="AKTEST",
            is_admin=False,
            is_superadmin=False,
        )
        mock_req = MagicMock(spec=web.Request)
        storage: dict[str, Any] = {
            "keypair": {"access_key": "AKTEST", "resource_policy": "default"},
        }
        mock_req.__getitem__ = lambda _, key: storage[key]
        req_ctx = RequestCtx(request=mock_req)
        mock_result, _ = self._create_mock_result()
        mock_processors.resource_preset.check_presets.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await handler.check_presets(body, user_context, req_ctx)

        response_body = response.to_json
        assert response_body is not None
        assert isinstance(response_body, dict)
        resource_slot_fields = [
            "keypair_limits",
            "keypair_using",
            "keypair_remaining",
            "group_limits",
            "group_using",
            "group_remaining",
            "scaling_group_remaining",
        ]
        for field in resource_slot_fields:
            assert isinstance(response_body[field], str)
            parsed = json.loads(response_body[field])
            assert isinstance(parsed, dict)
