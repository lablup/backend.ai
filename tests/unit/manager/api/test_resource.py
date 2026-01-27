"""
Tests for resource.py API handlers.

TODO: Currently auth decorators (auth_required, superadmin_required) are bypassed
      by mocking request.get(). This should be refactored to use proper middleware
      integration for more realistic testing.
"""

from __future__ import annotations

import json
import uuid
from http import HTTPStatus
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest
from aiohttp import web

from ai.backend.common.types import LegacyResourceSlotState as ResourceSlotState
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.resource import (
    admin_month_stats,
    check_presets,
    get_container_registries,
    get_watcher_status,
    list_presets,
    recalculate_usage,
    usage_per_month,
    usage_per_period,
    user_month_stats,
    watcher_agent_restart,
    watcher_agent_start,
    watcher_agent_stop,
)
from ai.backend.manager.errors.auth import AuthorizationFailed

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
    storage: dict[str, Any] = {}
    req.__getitem__ = lambda _, key: storage[key]
    req.__setitem__ = lambda _, key, value: storage.__setitem__(key, value)
    return req


@pytest.fixture
def superadmin_request(mock_root_ctx: MagicMock) -> MagicMock:
    """Mock request for superadmin user."""
    req = MagicMock(spec=web.Request)
    req.app = {"_root.context": mock_root_ctx}
    req.get = lambda k, default=None: {
        "is_authorized": True,
        "is_superadmin": True,
    }.get(k, default)
    return req


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestRecalculateUsage:
    """Tests for recalculate_usage handler."""

    @pytest.mark.asyncio
    async def test_calls_processor(
        self,
        superadmin_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and returns empty dict."""
        mock_root_ctx.processors.agent.recalculate_usage.wait_for_complete = AsyncMock()

        response = await recalculate_usage(superadmin_request)

        mock_root_ctx.processors.agent.recalculate_usage.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        # Verify response body is empty dict
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == {}

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await recalculate_usage(authorized_request)


class TestAdminMonthStats:
    """Tests for admin_month_stats handler."""

    @pytest.mark.asyncio
    async def test_calls_processor_and_returns_stats(
        self,
        superadmin_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor is called and stats are returned."""
        expected_stats = [{"date": "2024-01-01", "count": 10}]
        mock_result = MagicMock()
        mock_result.stats = expected_stats
        mock_root_ctx.processors.user.admin_month_stats.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await admin_month_stats(superadmin_request)

        mock_root_ctx.processors.user.admin_month_stats.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected stats
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_stats

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await admin_month_stats(authorized_request)


class TestGetContainerRegistries:
    """Tests for get_container_registries handler."""

    @pytest.mark.asyncio
    async def test_returns_registries_from_result(
        self,
        superadmin_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify result.registries is returned as JSON response."""
        expected_registries = {"docker.io": {"url": "https://docker.io"}}
        mock_result = MagicMock()
        mock_result.registries = expected_registries
        mock_root_ctx.processors.container_registry.get_container_registries.wait_for_complete = (
            AsyncMock(return_value=mock_result)
        )

        response = await get_container_registries(superadmin_request)

        mock_root_ctx.processors.container_registry.get_container_registries.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected registries
        json_response = cast(web.Response, response)
        assert json_response.body is not None
        response_body = json.loads(cast(bytes, json_response.body))
        assert response_body == expected_registries

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await get_container_registries(authorized_request)


class TestListPresets:
    """Tests for list_presets handler."""

    @pytest.mark.asyncio
    async def test_returns_presets_from_processor(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify processor result is returned as JSON response."""
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        authorized_request.query = {}
        expected_presets = [{"name": "small", "resource_slots": {}}]
        mock_result = MagicMock()
        mock_result.presets = expected_presets
        mock_root_ctx.processors.resource_preset.list_presets.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await list_presets(authorized_request)

        mock_root_ctx.processors.resource_preset.list_presets.wait_for_complete.assert_called_once()
        assert response.status == HTTPStatus.OK
        # Verify response body contains presets wrapped in dict
        json_response = cast(web.Response, response)
        assert json_response.body is not None
        response_body = json.loads(cast(bytes, json_response.body))
        assert response_body == {"presets": expected_presets}

    @pytest.mark.asyncio
    async def test_passes_scaling_group_from_query(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify scaling_group query param is passed to Action."""
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        authorized_request.query = {"scaling_group": "sg-test"}
        mock_result = MagicMock()
        mock_result.presets = []
        mock_root_ctx.processors.resource_preset.list_presets.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        await list_presets(authorized_request)

        call_args = (
            mock_root_ctx.processors.resource_preset.list_presets.wait_for_complete.call_args
        )
        action = call_args[0][0]
        assert action.scaling_group == "sg-test"

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await list_presets(unauthorized_request)


class TestUserMonthStats:
    """Tests for user_month_stats handler."""

    @pytest.mark.asyncio
    async def test_passes_user_uuid_to_action_and_returns_stats(
        self,
        authorized_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify user_id is passed to Action and stats are returned."""
        user_uuid = uuid.uuid4()
        authorized_request["keypair"] = {"access_key": "AKTEST"}
        authorized_request["user"] = {"uuid": user_uuid}
        expected_stats = [{"date": "2024-01-15", "usage": 100}]
        mock_result = MagicMock()
        mock_result.stats = expected_stats
        mock_root_ctx.processors.user.user_month_stats.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await user_month_stats(authorized_request)

        call_args = mock_root_ctx.processors.user.user_month_stats.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.user_id == user_uuid
        # Verify response body contains expected stats
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_stats

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await user_month_stats(unauthorized_request)


class TestGetWatcherStatus:
    """Tests for get_watcher_status handler."""

    @pytest.fixture
    def mock_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for superadmin user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        return req

    @pytest.mark.asyncio
    async def test_passes_agent_id_to_action_and_returns_data(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify agent_id is passed to Action and data is returned."""
        mock_request.text = AsyncMock(return_value=json.dumps({"agent_id": "agent-001"}))
        expected_data = {"status": "running"}
        mock_result = MagicMock()
        mock_result.data = expected_data
        mock_root_ctx.processors.agent.get_watcher_status.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await get_watcher_status(mock_request)

        call_args = mock_root_ctx.processors.agent.get_watcher_status.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.agent_id == "agent-001"
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected data
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_data

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await get_watcher_status(authorized_request)


class TestWatcherAgentStart:
    """Tests for watcher_agent_start handler."""

    @pytest.fixture
    def mock_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for superadmin user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        return req

    @pytest.mark.asyncio
    async def test_calls_processor_with_agent_id_and_returns_data(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify agent_id is passed to Action and data is returned."""
        mock_request.text = AsyncMock(return_value=json.dumps({"agent_id": "agent-001"}))
        expected_data = {"started": True}
        mock_result = MagicMock()
        mock_result.data = expected_data
        mock_root_ctx.processors.agent.watcher_agent_start.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await watcher_agent_start(mock_request)

        call_args = mock_root_ctx.processors.agent.watcher_agent_start.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.agent_id == "agent-001"
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected data
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_data

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await watcher_agent_start(authorized_request)


class TestWatcherAgentStop:
    """Tests for watcher_agent_stop handler."""

    @pytest.fixture
    def mock_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for superadmin user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        return req

    @pytest.mark.asyncio
    async def test_calls_processor_with_agent_id_and_returns_data(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify agent_id is passed to Action and data is returned."""
        mock_request.text = AsyncMock(return_value=json.dumps({"agent_id": "agent-001"}))
        expected_data = {"stopped": True}
        mock_result = MagicMock()
        mock_result.data = expected_data
        mock_root_ctx.processors.agent.watcher_agent_stop.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await watcher_agent_stop(mock_request)

        call_args = mock_root_ctx.processors.agent.watcher_agent_stop.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.agent_id == "agent-001"
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected data
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_data

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await watcher_agent_stop(authorized_request)


class TestWatcherAgentRestart:
    """Tests for watcher_agent_restart handler."""

    @pytest.fixture
    def mock_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for superadmin user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        return req

    @pytest.mark.asyncio
    async def test_calls_processor_with_agent_id_and_returns_data(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify agent_id is passed to Action and data is returned."""
        mock_request.text = AsyncMock(return_value=json.dumps({"agent_id": "agent-001"}))
        expected_data = {"restarted": True}
        mock_result = MagicMock()
        mock_result.data = expected_data
        mock_root_ctx.processors.agent.watcher_agent_restart.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await watcher_agent_restart(mock_request)

        call_args = mock_root_ctx.processors.agent.watcher_agent_restart.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.agent_id == "agent-001"
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected data
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_data

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await watcher_agent_restart(authorized_request)


class TestUsagePerMonth:
    """Tests for usage_per_month handler."""

    @pytest.fixture
    def mock_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for superadmin user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        return req

    @pytest.mark.asyncio
    async def test_passes_group_ids_and_month_to_action_and_returns_result(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify group_ids and month are passed to Action and result is returned."""
        mock_request.text = AsyncMock(
            return_value=json.dumps({"group_ids": "group-1,group-2", "month": "202401"})
        )
        expected_result = [{"group_id": "group-1", "usage": 100}]
        mock_result = MagicMock()
        mock_result.result = expected_result
        mock_root_ctx.processors.group.usage_per_month.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await usage_per_month(mock_request)

        call_args = mock_root_ctx.processors.group.usage_per_month.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.group_ids == ["group-1", "group-2"]
        assert action.month == "202401"
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected result
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_result

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await usage_per_month(authorized_request)


class TestUsagePerPeriod:
    """Tests for usage_per_period handler."""

    @pytest.fixture
    def mock_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for superadmin user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": True,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        return req

    @pytest.mark.asyncio
    async def test_passes_dates_to_action_and_returns_result(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify start_date and end_date are passed to Action and result is returned."""
        mock_request.text = AsyncMock(
            return_value=json.dumps({
                "project_id": "proj-1",
                "start_date": "20240101",
                "end_date": "20240131",
            })
        )
        expected_result = [{"date": "20240115", "usage": 50}]
        mock_result = MagicMock()
        mock_result.result = expected_result
        mock_root_ctx.processors.group.usage_per_period.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await usage_per_period(mock_request)

        call_args = mock_root_ctx.processors.group.usage_per_period.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.project_id == "proj-1"
        assert action.start_date == "20240101"
        assert action.end_date == "20240131"
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected result
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body == expected_result

    @pytest.mark.asyncio
    async def test_project_id_default_is_none(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify project_id defaults to None."""
        mock_request.text = AsyncMock(
            return_value=json.dumps({
                "start_date": "20240101",
                "end_date": "20240131",
            })
        )
        mock_result = MagicMock()
        mock_result.result = {"usage": []}
        mock_root_ctx.processors.group.usage_per_period.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        await usage_per_period(mock_request)

        call_args = mock_root_ctx.processors.group.usage_per_period.wait_for_complete.call_args
        action = call_args[0][0]
        assert action.project_id is None

    @pytest.mark.asyncio
    async def test_rejects_non_superadmin_request(
        self,
        authorized_request: MagicMock,
    ) -> None:
        """Verify non-superadmin request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await usage_per_period(authorized_request)


class TestCheckPresets:
    """Tests for check_presets handler."""

    @pytest.fixture
    def mock_request(self, mock_root_ctx: MagicMock) -> MagicMock:
        """Mock POST request for authenticated user."""
        req = MagicMock(spec=web.Request)
        req.app = {"_root.context": mock_root_ctx}
        req.get = lambda k, default=None: {
            "is_authorized": True,
            "is_superadmin": False,
        }.get(k, default)
        type(req).can_read_body = PropertyMock(return_value=True)
        req.method = "POST"
        req.content_type = "application/json"
        # Enable dict-like access for request["keypair"], request["user"]
        storage: dict[str, Any] = {}
        req.__getitem__ = lambda _, key: storage[key]
        req.__setitem__ = lambda _, key, value: storage.__setitem__(key, value)
        return req

    def _create_mock_result(self) -> tuple[MagicMock, MagicMock]:
        """Create a mock CheckResourcePresetsResult with mock slot."""
        mock_slot = MagicMock()
        mock_slot.to_json.return_value = {"cpu": "1", "mem": "1073741824"}
        mock_result = MagicMock()
        mock_result.presets = [{"name": "small"}]
        mock_result.keypair_limits = mock_slot
        mock_result.keypair_using = mock_slot
        mock_result.keypair_remaining = mock_slot
        mock_result.group_limits = mock_slot
        mock_result.group_using = mock_slot
        mock_result.group_remaining = mock_slot
        mock_result.scaling_group_remaining = mock_slot
        mock_result.scaling_groups = {
            "sg-test": {
                ResourceSlotState.OCCUPIED: mock_slot,
                ResourceSlotState.AVAILABLE: mock_slot,
            }
        }
        return mock_result, mock_slot

    @pytest.mark.asyncio
    async def test_passes_params_to_action_and_returns_response(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify group, scaling_group, access_key etc. are passed to Action and response is returned."""
        user_uuid = uuid.uuid4()
        mock_request.text = AsyncMock(
            return_value=json.dumps({"scaling_group": "sg-test", "group": "test-group"})
        )
        mock_request["keypair"] = {"access_key": "AKTEST", "resource_policy": "default"}
        mock_request["user"] = {"uuid": user_uuid, "domain_name": "default"}
        mock_result, mock_slot = self._create_mock_result()
        mock_root_ctx.processors.resource_preset.check_presets.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        response = await check_presets(mock_request)

        call_args = (
            mock_root_ctx.processors.resource_preset.check_presets.wait_for_complete.call_args
        )
        action = call_args[0][0]
        assert action.access_key == "AKTEST"
        assert action.resource_policy == "default"
        assert action.domain_name == "default"
        assert action.user_id == user_uuid
        assert action.group == "test-group"
        assert action.scaling_group == "sg-test"
        assert response.status == HTTPStatus.OK
        # Verify response body contains expected structure
        assert response.body is not None
        response_body = json.loads(cast(bytes, response.body))
        assert response_body["presets"] == [{"name": "small"}]
        assert response_body["keypair_limits"] == mock_slot.to_json()
        assert response_body["keypair_using"] == mock_slot.to_json()
        assert response_body["keypair_remaining"] == mock_slot.to_json()
        assert response_body["group_limits"] == mock_slot.to_json()
        assert response_body["group_using"] == mock_slot.to_json()
        assert response_body["group_remaining"] == mock_slot.to_json()
        assert response_body["scaling_group_remaining"] == mock_slot.to_json()

    @pytest.mark.asyncio
    async def test_converts_resource_slots_to_json(
        self,
        mock_request: MagicMock,
        mock_root_ctx: MagicMock,
    ) -> None:
        """Verify ResourceSlot.to_json() is called for response conversion."""
        user_uuid = uuid.uuid4()
        mock_request.text = AsyncMock(
            return_value=json.dumps({"scaling_group": "sg-test", "group": "default"})
        )
        mock_request["keypair"] = {"access_key": "AKTEST", "resource_policy": "default"}
        mock_request["user"] = {"uuid": user_uuid, "domain_name": "default"}
        mock_result, mock_slot = self._create_mock_result()
        mock_root_ctx.processors.resource_preset.check_presets.wait_for_complete = AsyncMock(
            return_value=mock_result
        )

        await check_presets(mock_request)

        # to_json() should be called for multiple fields (keypair_limits, keypair_using, etc.)
        assert mock_slot.to_json.call_count >= 7

    @pytest.mark.asyncio
    async def test_rejects_unauthorized_request(
        self,
        unauthorized_request: MagicMock,
    ) -> None:
        """Verify unauthorized request is rejected."""
        with pytest.raises(AuthorizationFailed):
            await check_presets(unauthorized_request)
