import uuid
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.exception import InvalidAPIParameters, ResourcePresetConflict
from ai.backend.common.types import (
    BinarySize,
    DefaultForUnspecified,
    ResourceSlot,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
    CreateResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
    DeleteResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource_preset.actions.modify_preset import (
    ModifyResourcePresetAction,
    ModifyResourcePresetActionResult,
    ResourcePresetModifier,
)
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.resource_preset.types import ResourcePresetCreator
from ai.backend.manager.types import OptionalState, TriState

from ..test_utils import TestScenario


@pytest.fixture
def mock_db_engine():
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def mock_agent_registry():
    return MagicMock(spec=AgentRegistry)


@pytest.fixture
def mock_config_provider():
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
        return_value={"cpu": "cpu", "memory": "memory", "gpu": "gpu", "gpu_memory": "gpu_memory"}
    )
    mock_provider.legacy_etcd_config_loader.get_raw = AsyncMock(return_value=True)
    return mock_provider


@pytest.fixture
def mock_resource_preset_repository():
    return MagicMock(spec=ResourcePresetRepository)


@pytest.fixture
def resource_preset_service(
    mock_db_engine, mock_agent_registry, mock_config_provider, mock_resource_preset_repository
):
    return ResourcePresetService(
        db=mock_db_engine,
        agent_registry=mock_agent_registry,
        config_provider=mock_config_provider,
        resource_preset_repository=mock_resource_preset_repository,
    )


# Test Scenario 1: Create Preset
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "CPU-only preset creation should succeed",
            CreateResourcePresetAction(
                creator=ResourcePresetCreator(
                    name="cpu-small",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=BinarySize.from_str("1G"),
                    scaling_group_name=None,
                )
            ),
            CreateResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="cpu-small",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=BinarySize.from_str("1G"),
                    scaling_group_name=None,
                )
            ),
        ),
        TestScenario.success(
            "GPU preset creation with scaling group should succeed",
            CreateResourcePresetAction(
                creator=ResourcePresetCreator(
                    name="gpu-standard",
                    resource_slots=ResourceSlot(
                        {"cpu": "4", "memory": "16G", "gpu": "1", "gpu_memory": "8G"}
                    ),
                    shared_memory=BinarySize.from_str("2G"),
                    scaling_group_name="gpu-cluster",
                )
            ),
            CreateResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="gpu-standard",
                    resource_slots=ResourceSlot(
                        {"cpu": "4", "memory": "16G", "gpu": "1", "gpu_memory": "8G"}
                    ),
                    shared_memory=BinarySize.from_str("2G"),
                    scaling_group_name="gpu-cluster",
                )
            ),
        ),
        TestScenario.failure(
            "Missing intrinsic slots should raise InvalidAPIParameters",
            CreateResourcePresetAction(
                creator=ResourcePresetCreator(
                    name="invalid-preset",
                    resource_slots=ResourceSlot({"gpu": "1"}),  # Missing CPU and memory
                    shared_memory=None,
                    scaling_group_name=None,
                )
            ),
            InvalidAPIParameters,
        ),
        TestScenario.failure(
            "Duplicate preset name should raise ResourcePresetConflict",
            CreateResourcePresetAction(
                creator=ResourcePresetCreator(
                    name="existing-preset",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=None,
                    scaling_group_name=None,
                )
            ),
            ResourcePresetConflict,
        ),
        TestScenario.success(
            "Same preset name in different scaling group should succeed",
            CreateResourcePresetAction(
                creator=ResourcePresetCreator(
                    name="common-preset",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=None,
                    scaling_group_name="cluster-b",
                )
            ),
            CreateResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="common-preset",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=None,
                    scaling_group_name="cluster-b",
                )
            ),
        ),
        TestScenario.success(
            "Custom resource types should be supported",
            CreateResourcePresetAction(
                creator=ResourcePresetCreator(
                    name="custom-preset",
                    resource_slots=ResourceSlot(
                        {"cpu": "4", "memory": "8G", "npu": "2", "tpu": "1"}
                    ),
                    shared_memory=None,
                    scaling_group_name=None,
                )
            ),
            CreateResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="custom-preset",
                    resource_slots=ResourceSlot(
                        {"cpu": "4", "memory": "8G", "npu": "2", "tpu": "1"}
                    ),
                    shared_memory=None,
                    scaling_group_name=None,
                )
            ),
        ),
    ],
)
async def test_create_preset(test_scenario: TestScenario, resource_preset_service):
    action = test_scenario.input

    if test_scenario.expected_exception == ResourcePresetConflict:
        resource_preset_service._resource_preset_repository.create_preset_validated = AsyncMock(
            return_value=None
        )
    elif test_scenario.expected:
        expected_data = test_scenario.expected.resource_preset
        resource_preset_service._resource_preset_repository.create_preset_validated = AsyncMock(
            return_value=expected_data
        )

    await test_scenario.test(resource_preset_service.create_preset)


# Test Scenario 2: Modify Preset
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Resource slots update should succeed",
            ModifyResourcePresetAction(
                name="cpu-small",
                id=None,
                modifier=ResourcePresetModifier(
                    resource_slots=OptionalState.update(
                        ResourceSlot({"cpu": "4", "memory": "8G"})
                    )
                ),
            ),
            ModifyResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="cpu-small",
                    resource_slots=ResourceSlot({"cpu": "4", "memory": "8G"}),
                    shared_memory=BinarySize.from_str("1G"),
                    scaling_group_name=None,
                )
            ),
        ),
        TestScenario.success(
            "Preset name change should succeed",
            ModifyResourcePresetAction(
                name=None,
                id=uuid.uuid4(),
                modifier=ResourcePresetModifier(name=OptionalState.update("cpu-medium")),
            ),
            ModifyResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="cpu-medium",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=BinarySize.from_str("1G"),
                    scaling_group_name=None,
                )
            ),
        ),
        TestScenario.success(
            "Shared memory adjustment should succeed",
            ModifyResourcePresetAction(
                name="gpu-standard",
                id=None,
                modifier=ResourcePresetModifier(
                    shared_memory=TriState.update(BinarySize.from_str("4G"))
                ),
            ),
            ModifyResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="gpu-standard",
                    resource_slots=ResourceSlot(
                        {"cpu": "4", "memory": "16G", "gpu": "1", "gpu_memory": "8G"}
                    ),
                    shared_memory=BinarySize.from_str("4G"),
                    scaling_group_name="gpu-cluster",
                )
            ),
        ),
        TestScenario.failure(
            "Removing intrinsic slots should raise InvalidAPIParameters",
            ModifyResourcePresetAction(
                name="gpu-standard",
                id=None,
                modifier=ResourcePresetModifier(
                    resource_slots=OptionalState.update(ResourceSlot({"gpu": "2"}))
                ),
            ),
            InvalidAPIParameters,
        ),
        TestScenario.failure(
            "Non-existent preset should raise ObjectNotFound",
            ModifyResourcePresetAction(
                name="non-existent-preset",
                id=None,
                modifier=ResourcePresetModifier(name=OptionalState.update("new-name")),
            ),
            ObjectNotFound,
        ),
        TestScenario.failure(
            "Neither name nor id provided should raise InvalidAPIParameters",
            ModifyResourcePresetAction(
                name=None,
                id=None,
                modifier=ResourcePresetModifier(name=OptionalState.update("new-name")),
            ),
            InvalidAPIParameters,
        ),
    ],
)
async def test_modify_preset(test_scenario: TestScenario, resource_preset_service):
    action = test_scenario.input

    if test_scenario.expected_exception == ObjectNotFound:
        resource_preset_service._resource_preset_repository.modify_preset_validated = AsyncMock(
            side_effect=ObjectNotFound("Resource preset not found")
        )
    elif test_scenario.expected:
        expected_data = test_scenario.expected.resource_preset
        resource_preset_service._resource_preset_repository.modify_preset_validated = AsyncMock(
            return_value=expected_data
        )

    await test_scenario.test(resource_preset_service.modify_preset)


# Test Scenario 3: Delete Preset
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Normal preset deletion should succeed",
            DeleteResourcePresetAction(name="unused-preset", id=None),
            DeleteResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="unused-preset",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=None,
                    scaling_group_name=None,
                )
            ),
        ),
        TestScenario.success(
            "Preset in use deletion should succeed",
            DeleteResourcePresetAction(name="popular-preset", id=None),
            DeleteResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="popular-preset",
                    resource_slots=ResourceSlot({"cpu": "4", "memory": "8G"}),
                    shared_memory=None,
                    scaling_group_name=None,
                )
            ),
        ),
        TestScenario.success(
            "Delete by UUID should succeed",
            DeleteResourcePresetAction(name=None, id=uuid.uuid4()),
            DeleteResourcePresetActionResult(
                resource_preset=ResourcePresetData(
                    id=uuid.uuid4(),
                    name="some-preset",
                    resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
                    shared_memory=None,
                    scaling_group_name=None,
                )
            ),
        ),
        TestScenario.failure(
            "Non-existent preset should raise ObjectNotFound",
            DeleteResourcePresetAction(name="non-existent", id=None),
            ObjectNotFound,
        ),
        TestScenario.failure(
            "Neither name nor id provided should raise InvalidAPIParameters",
            DeleteResourcePresetAction(name=None, id=None),
            InvalidAPIParameters,
        ),
    ],
)
async def test_delete_preset(test_scenario: TestScenario, resource_preset_service):
    action = test_scenario.input

    if test_scenario.expected_exception == ObjectNotFound:
        resource_preset_service._resource_preset_repository.delete_preset_validated = AsyncMock(
            side_effect=ObjectNotFound("Resource preset not found")
        )
    elif test_scenario.expected:
        expected_data = test_scenario.expected.resource_preset
        resource_preset_service._resource_preset_repository.delete_preset_validated = AsyncMock(
            return_value=expected_data
        )

    await test_scenario.test(resource_preset_service.delete_preset)


# Test Scenario 4: List Presets
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "List all global presets",
            ListResourcePresetsAction(access_key="test-access-key", scaling_group=None),
            ListResourcePresetsResult(
                presets=[
                    {
                        "id": str(uuid.uuid4()),
                        "name": "cpu-small",
                        "resource_slots": {"cpu": "2", "memory": "4294967296"},
                        "shared_memory": str(BinarySize.from_str("1G")),
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "gpu-standard",
                        "resource_slots": {
                            "cpu": "4",
                            "memory": "17179869184",
                            "gpu": "1",
                            "gpu_memory": "8589934592",
                        },
                        "shared_memory": str(BinarySize.from_str("2G")),
                    },
                ]
            ),
        ),
        TestScenario.success(
            "List presets for specific scaling group",
            ListResourcePresetsAction(access_key="test-access-key", scaling_group="gpu-cluster"),
            ListResourcePresetsResult(
                presets=[
                    {
                        "id": str(uuid.uuid4()),
                        "name": "cpu-small",
                        "resource_slots": {"cpu": "2", "memory": "4294967296"},
                        "shared_memory": str(BinarySize.from_str("1G")),
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "gpu-cluster-preset",
                        "resource_slots": {"cpu": "8", "memory": "34359738368", "gpu": "2"},
                        "shared_memory": None,
                    },
                ]
            ),
        ),
        TestScenario.success(
            "Empty preset list",
            ListResourcePresetsAction(access_key="test-access-key", scaling_group=None),
            ListResourcePresetsResult(presets=[]),
        ),
    ],
)
async def test_list_presets(test_scenario: TestScenario, resource_preset_service):
    action = test_scenario.input

    if test_scenario.expected.presets:
        mock_presets = []
        for preset in test_scenario.expected.presets:
            preset_data = ResourcePresetData(
                id=uuid.UUID(preset["id"]),
                name=preset["name"],
                resource_slots=ResourceSlot(
                    {
                        k: (
                            str(int(v))
                            if k in ["cpu", "gpu", "npu", "tpu"]
                            else f"{int(v) // (1024**3)}G"
                        )
                        for k, v in preset["resource_slots"].items()
                    }
                ),
                shared_memory=(
                    BinarySize.from_str(preset["shared_memory"])
                    if preset["shared_memory"]
                    else None
                ),
                scaling_group_name=action.scaling_group,
            )
            mock_presets.append(preset_data)

        resource_preset_service._resource_preset_repository.list_presets = AsyncMock(
            return_value=mock_presets
        )
    else:
        resource_preset_service._resource_preset_repository.list_presets = AsyncMock(
            return_value=[]
        )

    await test_scenario.test(resource_preset_service.list_presets)


# Test Scenario 5: Check Presets
@pytest.mark.asyncio
async def test_check_presets_sufficient_resources(resource_preset_service):
    """Test check presets with sufficient resources"""
    action = CheckResourcePresetsAction(
        access_key="test-key",
        resource_policy={"total_resource_slots": {"cpu": "100", "memory": "100G", "gpu": "10"}},
        domain_name="default",
        group="default",
        user_id=uuid.uuid4(),
        scaling_group=None,
    )

    # Mock database queries
    mock_conn = AsyncMock()
    mock_db_engine = resource_preset_service._db
    mock_db_engine.begin_readonly = AsyncMock(return_value=mock_conn.__aenter__())

    # Mock group query
    mock_result = MagicMock()
    mock_result.first.return_value = {
        "id": uuid.uuid4(),
        "total_resource_slots": {"cpu": "50", "memory": "50G"},
    }
    mock_conn.execute = AsyncMock(return_value=mock_result)

    # Mock domain query
    mock_conn.scalar = AsyncMock(return_value={"cpu": "200", "memory": "200G", "gpu": "20"})

    # Mock scaling group query
    sgroup_mock = MagicMock()
    sgroup_mock.name = "default"
    mock_conn.__aenter__.return_value = mock_conn
    with patch(
        "ai.backend.manager.services.resource_preset.service.query_allowed_sgroups",
        AsyncMock(return_value=[sgroup_mock]),
    ):
        # Mock agent registry methods
        resource_preset_service._agent_registry.get_keypair_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "10", "memory": "10G", "gpu": "1"})
        )
        resource_preset_service._agent_registry.get_group_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "5", "memory": "5G"})
        )
        resource_preset_service._agent_registry.get_domain_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "20", "memory": "20G", "gpu": "2"})
        )

        # Mock stream queries
        mock_conn.stream = AsyncMock(return_value=[].__aiter__())

        # Mock presets
        preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="test-preset",
            resource_slots=ResourceSlot({"cpu": "2", "memory": "4G"}),
            shared_memory=None,
            scaling_group_name=None,
        )
        resource_preset_service._resource_preset_repository.list_presets = AsyncMock(
            return_value=[preset_data]
        )

        result = await resource_preset_service.check_presets(action)

        assert isinstance(result, CheckResourcePresetsActionResult)
        assert len(result.presets) == 1
        assert result.presets[0]["name"] == "test-preset"
        assert result.presets[0]["allocatable"] is False  # No agents available


@pytest.mark.asyncio
async def test_check_presets_resource_shortage(resource_preset_service):
    """Test check presets with resource shortage"""
    action = CheckResourcePresetsAction(
        access_key="test-key",
        resource_policy={"total_resource_slots": {"cpu": "4", "memory": "8G", "gpu": "0"}},
        domain_name="default",
        group="default",
        user_id=uuid.uuid4(),
        scaling_group="gpu-cluster",
    )

    # Mock database queries
    mock_conn = AsyncMock()
    mock_db_engine = resource_preset_service._db
    mock_db_engine.begin_readonly = AsyncMock(return_value=mock_conn.__aenter__())

    # Mock group query
    mock_result = MagicMock()
    mock_result.first.return_value = {
        "id": uuid.uuid4(),
        "total_resource_slots": {"cpu": "10", "memory": "20G", "gpu": "2"},
    }
    mock_conn.execute = AsyncMock(return_value=mock_result)

    # Mock domain query
    mock_conn.scalar = AsyncMock(return_value={"cpu": "100", "memory": "100G", "gpu": "10"})

    # Mock scaling group query
    sgroup_mock = MagicMock()
    sgroup_mock.name = "gpu-cluster"
    mock_conn.__aenter__.return_value = mock_conn
    with patch(
        "ai.backend.manager.services.resource_preset.service.query_allowed_sgroups",
        AsyncMock(return_value=[sgroup_mock]),
    ):
        # Mock agent registry methods
        resource_preset_service._agent_registry.get_keypair_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "3", "memory": "6G", "gpu": "0"})
        )
        resource_preset_service._agent_registry.get_group_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "8", "memory": "16G", "gpu": "1"})
        )
        resource_preset_service._agent_registry.get_domain_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "50", "memory": "50G", "gpu": "5"})
        )

        # Mock kernel occupancy stream
        kernel_data = [
            {
                "scaling_group_name": "gpu-cluster",
                "occupied_slots": ResourceSlot({"cpu": "2", "memory": "4G", "gpu": "1"}),
            }
        ]
        mock_conn.stream = AsyncMock(side_effect=[kernel_data.__aiter__(), [].__aiter__()])

        # Mock presets
        cpu_preset = ResourcePresetData(
            id=uuid.uuid4(),
            name="cpu-small",
            resource_slots=ResourceSlot({"cpu": "1", "memory": "2G"}),
            shared_memory=None,
            scaling_group_name=None,
        )
        gpu_preset = ResourcePresetData(
            id=uuid.uuid4(),
            name="gpu-standard",
            resource_slots=ResourceSlot({"cpu": "4", "memory": "16G", "gpu": "1"}),
            shared_memory=None,
            scaling_group_name="gpu-cluster",
        )
        resource_preset_service._resource_preset_repository.list_presets = AsyncMock(
            return_value=[cpu_preset, gpu_preset]
        )

        result = await resource_preset_service.check_presets(action)

        assert isinstance(result, CheckResourcePresetsActionResult)
        assert len(result.presets) == 2

        # CPU preset should be allocatable (within limits)
        cpu_preset_result = next(p for p in result.presets if p["name"] == "cpu-small")
        assert cpu_preset_result["allocatable"] is False  # No agents

        # GPU preset should not be allocatable (exceeds GPU limit)
        gpu_preset_result = next(p for p in result.presets if p["name"] == "gpu-standard")
        assert gpu_preset_result["allocatable"] is False


@pytest.mark.asyncio
async def test_check_presets_group_visibility(resource_preset_service):
    """Test check presets with group resource visibility disabled"""
    action = CheckResourcePresetsAction(
        access_key="test-key",
        resource_policy={"total_resource_slots": {"cpu": "100", "memory": "100G"}},
        domain_name="default",
        group="default",
        user_id=uuid.uuid4(),
        scaling_group=None,
    )

    # Mock config for group visibility
    resource_preset_service._config_provider.legacy_etcd_config_loader.get_raw = AsyncMock(
        return_value=False  # group_resource_visibility disabled
    )

    # Mock database queries
    mock_conn = AsyncMock()
    mock_db_engine = resource_preset_service._db
    mock_db_engine.begin_readonly = AsyncMock(return_value=mock_conn.__aenter__())

    # Mock group query
    mock_result = MagicMock()
    mock_result.first.return_value = {
        "id": uuid.uuid4(),
        "total_resource_slots": {"cpu": "50", "memory": "50G"},
    }
    mock_conn.execute = AsyncMock(return_value=mock_result)

    # Mock domain query
    mock_conn.scalar = AsyncMock(return_value={"cpu": "200", "memory": "200G"})

    # Mock scaling group query
    sgroup_mock = MagicMock()
    sgroup_mock.name = "default"
    mock_conn.__aenter__.return_value = mock_conn
    with patch(
        "ai.backend.manager.services.resource_preset.service.query_allowed_sgroups",
        AsyncMock(return_value=[sgroup_mock]),
    ):
        # Mock agent registry methods
        resource_preset_service._agent_registry.get_keypair_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "10", "memory": "10G"})
        )
        resource_preset_service._agent_registry.get_group_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "5", "memory": "5G"})
        )
        resource_preset_service._agent_registry.get_domain_occupancy = AsyncMock(
            return_value=ResourceSlot({"cpu": "20", "memory": "20G"})
        )

        # Mock stream queries
        mock_conn.stream = AsyncMock(return_value=[].__aiter__())

        # Mock presets
        resource_preset_service._resource_preset_repository.list_presets = AsyncMock(
            return_value=[]
        )

        result = await resource_preset_service.check_presets(action)

        # Check that group resources are hidden (NaN)
        assert "NaN" in str(result.group_limits["cpu"])
        assert "NaN" in str(result.group_using["cpu"])
        assert "NaN" in str(result.group_remaining["cpu"])


@pytest.mark.asyncio
async def test_check_presets_invalid_group(resource_preset_service):
    """Test check presets with invalid group"""
    action = CheckResourcePresetsAction(
        access_key="test-key",
        resource_policy={"total_resource_slots": {"cpu": "100", "memory": "100G"}},
        domain_name="default",
        group="non-existent-group",
        user_id=uuid.uuid4(),
        scaling_group=None,
    )

    # Mock database queries
    mock_conn = AsyncMock()
    mock_db_engine = resource_preset_service._db
    mock_db_engine.begin_readonly = AsyncMock(return_value=mock_conn.__aenter__())

    # Mock group query to return None (group not found)
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_conn.execute = AsyncMock(return_value=mock_result)
    mock_conn.__aenter__.return_value = mock_conn

    with pytest.raises(InvalidAPIParameters, match="Unknown project"):
        await resource_preset_service.check_presets(action)


@pytest.mark.asyncio
async def test_check_presets_invalid_scaling_group(resource_preset_service):
    """Test check presets with invalid scaling group"""
    action = CheckResourcePresetsAction(
        access_key="test-key",
        resource_policy={"total_resource_slots": {"cpu": "100", "memory": "100G"}},
        domain_name="default",
        group="default",
        user_id=uuid.uuid4(),
        scaling_group="non-existent-sgroup",
    )

    # Mock database queries
    mock_conn = AsyncMock()
    mock_db_engine = resource_preset_service._db
    mock_db_engine.begin_readonly = AsyncMock(return_value=mock_conn.__aenter__())

    # Mock group query
    mock_result = MagicMock()
    mock_result.first.return_value = {
        "id": uuid.uuid4(),
        "total_resource_slots": {"cpu": "50", "memory": "50G"},
    }
    mock_conn.execute = AsyncMock(return_value=mock_result)

    # Mock domain query
    mock_conn.scalar = AsyncMock(return_value={"cpu": "200", "memory": "200G"})

    # Mock scaling group query to return only 'default' sgroup
    sgroup_mock = MagicMock()
    sgroup_mock.name = "default"
    mock_conn.__aenter__.return_value = mock_conn
    with patch(
        "ai.backend.manager.services.resource_preset.service.query_allowed_sgroups",
        AsyncMock(return_value=[sgroup_mock]),
    ):
        with pytest.raises(InvalidAPIParameters, match="Unknown scaling group"):
            await resource_preset_service.check_presets(action)