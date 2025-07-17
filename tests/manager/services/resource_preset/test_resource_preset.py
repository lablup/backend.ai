"""
Simple tests for Resource Preset Service functionality based on test scenarios.
Tests the core resource preset service actions to verify compatibility with test scenarios.
"""

import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.exception import InvalidAPIParameters, ResourcePresetConflict
from ai.backend.common.types import (
    BinarySize,
    ResourceSlot,
    SlotName,
    SlotTypes,
    current_resource_slots,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.common import ObjectNotFound
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


class TestResourcePresetServiceCompatibility:
    """Test compatibility of resource preset service with test scenarios."""

    @pytest.fixture
    def mock_dependencies(self) -> dict[str, Any]:
        """Create mocked dependencies for testing."""
        # Set up current_resource_slots context variable
        resource_slots = {
            SlotName("cpu"): SlotTypes("count"),
            SlotName("mem"): SlotTypes("bytes"),
            SlotName("memory"): SlotTypes("bytes"),
            SlotName("gpu"): SlotTypes("count"),
            SlotName("gpu_memory"): SlotTypes("bytes"),
            SlotName("npu"): SlotTypes("count"),
            SlotName("tpu"): SlotTypes("count"),
        }
        current_resource_slots.set(resource_slots)

        db_engine = MagicMock(spec=ExtendedAsyncSAEngine)
        agent_registry = MagicMock(spec=AgentRegistry)
        config_provider = MagicMock(spec=ManagerConfigProvider)
        resource_preset_repository = MagicMock(spec=ResourcePresetRepository)

        # Mock config provider methods
        config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value=resource_slots
        )
        config_provider.legacy_etcd_config_loader.get_raw = AsyncMock(return_value=True)

        return {
            "db": db_engine,
            "agent_registry": agent_registry,
            "config_provider": config_provider,
            "resource_preset_repository": resource_preset_repository,
        }

    @pytest.fixture
    def resource_preset_service(self, mock_dependencies) -> ResourcePresetService:
        """Create ResourcePresetService instance with mocked dependencies."""
        return ResourcePresetService(
            db=mock_dependencies["db"],
            agent_registry=mock_dependencies["agent_registry"],
            config_provider=mock_dependencies["config_provider"],
            resource_preset_repository=mock_dependencies["resource_preset_repository"],
        )

    @pytest.mark.asyncio
    async def test_create_preset_action_structure(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test that CreateResourcePresetAction has the expected structure from test scenarios."""
        # Mock successful preset creation
        mock_preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="cpu-small",
            resource_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
            shared_memory=BinarySize(BinarySize.from_str("1G")),
            scaling_group_name=None,
        )

        mock_dependencies["resource_preset_repository"].create_preset_validated = AsyncMock(
            return_value=mock_preset_data
        )

        # Test 1: Normal CPU-only preset creation
        action = CreateResourcePresetAction(
            creator=ResourcePresetCreator(
                name="cpu-small",
                resource_slots=ResourceSlot({"cpu": "2", "mem": "4G"}),
                shared_memory=str(BinarySize.from_str("1G")),
                scaling_group_name=None,
            )
        )

        result = await resource_preset_service.create_preset(action)

        assert isinstance(result, CreateResourcePresetActionResult)
        assert result.resource_preset is not None
        assert result.resource_preset.name == "cpu-small"
        mock_dependencies["resource_preset_repository"].create_preset_validated.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_gpu_preset_with_scaling_group(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test GPU preset creation with scaling group."""
        mock_preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="gpu-standard",
            resource_slots=ResourceSlot({
                "cpu": Decimal("4"),
                "mem": Decimal("17179869184"),
                "gpu": Decimal("1"),
                "gpu_memory": Decimal("8589934592"),
            }),
            shared_memory=BinarySize(BinarySize.from_str("2G")),
            scaling_group_name="gpu-cluster",
        )

        mock_dependencies["resource_preset_repository"].create_preset_validated = AsyncMock(
            return_value=mock_preset_data
        )

        action = CreateResourcePresetAction(
            creator=ResourcePresetCreator(
                name="gpu-standard",
                resource_slots=ResourceSlot({
                    "cpu": "4",
                    "mem": "16G",
                    "gpu": "1",
                    "gpu_memory": "8G",
                }),
                shared_memory=str(BinarySize.from_str("2G")),
                scaling_group_name="gpu-cluster",
            )
        )

        result = await resource_preset_service.create_preset(action)

        assert isinstance(result, CreateResourcePresetActionResult)
        assert result.resource_preset.scaling_group_name == "gpu-cluster"

    @pytest.mark.asyncio
    async def test_create_preset_missing_intrinsic_slots(self, resource_preset_service) -> None:
        """Test preset creation fails when missing intrinsic slots."""
        action = CreateResourcePresetAction(
            creator=ResourcePresetCreator(
                name="invalid-preset",
                resource_slots=ResourceSlot({"gpu": "1"}),  # Missing CPU and mem
                shared_memory=None,
                scaling_group_name=None,
            )
        )

        with pytest.raises(InvalidAPIParameters):
            await resource_preset_service.create_preset(action)

    @pytest.mark.asyncio
    async def test_create_duplicate_preset(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test duplicate preset name raises ResourcePresetConflict."""
        mock_dependencies["resource_preset_repository"].create_preset_validated = AsyncMock(
            return_value=None
        )

        action = CreateResourcePresetAction(
            creator=ResourcePresetCreator(
                name="existing-preset",
                resource_slots=ResourceSlot({"cpu": "2", "mem": "4G"}),
                shared_memory=None,
                scaling_group_name=None,
            )
        )

        with pytest.raises(ResourcePresetConflict):
            await resource_preset_service.create_preset(action)

    @pytest.mark.asyncio
    async def test_modify_preset_action_structure(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test that ModifyResourcePresetAction supports the expected modifications."""
        mock_preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="cpu-small",
            resource_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8589934592")}),
            shared_memory=BinarySize(BinarySize.from_str("1G")),
            scaling_group_name=None,
        )

        mock_dependencies["resource_preset_repository"].modify_preset_validated = AsyncMock(
            return_value=mock_preset_data
        )

        # Test resource slots update
        action = ModifyResourcePresetAction(
            name="cpu-small",
            id=None,
            modifier=ResourcePresetModifier(
                resource_slots=OptionalState.update(ResourceSlot({"cpu": "4", "mem": "8G"}))
            ),
        )

        result = await resource_preset_service.modify_preset(action)

        assert isinstance(result, ModifyResourcePresetActionResult)
        assert result.resource_preset is not None
        mock_dependencies["resource_preset_repository"].modify_preset_validated.assert_called_once()

    @pytest.mark.asyncio
    async def test_modify_preset_name_change(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test preset name modification."""
        preset_id = uuid.uuid4()
        mock_preset_data = ResourcePresetData(
            id=preset_id,
            name="cpu-medium",
            resource_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
            shared_memory=BinarySize(BinarySize.from_str("1G")),
            scaling_group_name=None,
        )

        mock_dependencies["resource_preset_repository"].modify_preset_validated = AsyncMock(
            return_value=mock_preset_data
        )

        action = ModifyResourcePresetAction(
            name=None,
            id=preset_id,
            modifier=ResourcePresetModifier(name=OptionalState.update("cpu-medium")),
        )

        result = await resource_preset_service.modify_preset(action)

        assert result.resource_preset.name == "cpu-medium"

    @pytest.mark.asyncio
    async def test_modify_preset_missing_identifiers(self, resource_preset_service) -> None:
        """Test modify fails when neither name nor id provided."""
        action = ModifyResourcePresetAction(
            name=None,
            id=None,
            modifier=ResourcePresetModifier(name=OptionalState.update("new-name")),
        )

        with pytest.raises(InvalidAPIParameters):
            await resource_preset_service.modify_preset(action)

    @pytest.mark.asyncio
    async def test_delete_preset_action_structure(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test that DeleteResourcePresetAction works as expected."""
        mock_preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="unused-preset",
            resource_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
            shared_memory=None,
            scaling_group_name=None,
        )

        mock_dependencies["resource_preset_repository"].delete_preset_validated = AsyncMock(
            return_value=mock_preset_data
        )

        action = DeleteResourcePresetAction(name="unused-preset", id=None)

        result = await resource_preset_service.delete_preset(action)

        assert isinstance(result, DeleteResourcePresetActionResult)
        assert result.resource_preset is not None
        mock_dependencies["resource_preset_repository"].delete_preset_validated.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_preset(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test delete non-existent preset raises ObjectNotFound."""
        mock_dependencies["resource_preset_repository"].delete_preset_validated = AsyncMock(
            side_effect=ObjectNotFound("Resource preset not found")
        )

        action = DeleteResourcePresetAction(name="non-existent", id=None)

        with pytest.raises(ObjectNotFound):
            await resource_preset_service.delete_preset(action)

    @pytest.mark.asyncio
    async def test_list_presets_action_structure(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test that ListResourcePresetsAction returns expected structure."""
        mock_presets = [
            ResourcePresetData(
                id=uuid.uuid4(),
                name="cpu-small",
                resource_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
                shared_memory=BinarySize(BinarySize.from_str("1G")),
                scaling_group_name=None,
            ),
            ResourcePresetData(
                id=uuid.uuid4(),
                name="gpu-standard",
                resource_slots=ResourceSlot({
                    "cpu": Decimal("4"),
                    "mem": Decimal("17179869184"),
                    "gpu": Decimal("1"),
                    "gpu_memory": Decimal("8589934592"),
                }),
                shared_memory=BinarySize(BinarySize.from_str("2G")),
                scaling_group_name=None,
            ),
        ]

        mock_dependencies["resource_preset_repository"].list_presets = AsyncMock(
            return_value=mock_presets
        )

        action = ListResourcePresetsAction(access_key="test-access-key", scaling_group=None)

        result = await resource_preset_service.list_presets(action)

        assert isinstance(result, ListResourcePresetsResult)
        assert len(result.presets) == 2
        assert result.presets[0]["name"] == "cpu-small"
        assert result.presets[1]["name"] == "gpu-standard"

        # Check that slots are normalized and converted to JSON format
        assert "cpu" in result.presets[0]["resource_slots"]
        assert "mem" in result.presets[0]["resource_slots"]
        assert "memory" in result.presets[0]["resource_slots"]  # Normalized slot
        assert "gpu" in result.presets[0]["resource_slots"]  # Default value

    @pytest.mark.asyncio
    async def test_check_presets_with_sufficient_resources(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test check presets when resources are sufficient."""
        action = CheckResourcePresetsAction(
            access_key="test-key",
            resource_policy={
                "total_resource_slots": {"cpu": "100", "mem": "100G", "gpu": "10"},
                "default_for_unspecified": "UNLIMITED",
            },
            domain_name="default",
            group="default",
            user_id=uuid.uuid4(),
            scaling_group=None,
        )

        # Setup complex mocking for check_presets
        await self._setup_check_presets_mocks(resource_preset_service, mock_dependencies, action)

        result = await resource_preset_service.check_presets(action)

        assert isinstance(result, CheckResourcePresetsActionResult)
        assert result.keypair_limits is not None
        assert result.group_limits is not None
        assert len(result.presets) > 0

    async def _setup_check_presets_mocks(self, service, deps, action) -> None:
        """Helper to setup complex mocks for check_presets tests."""
        # Mock database connection
        mock_conn = AsyncMock()
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)
        deps["db"].begin_readonly = MagicMock(return_value=mock_ctx)

        # Mock group query
        mock_result = MagicMock()
        mock_result.first.return_value = {
            "id": uuid.uuid4(),
            "total_resource_slots": {"cpu": "50", "mem": "50G"},
        }
        mock_conn.execute = AsyncMock(return_value=mock_result)

        # Mock domain query
        mock_conn.scalar = AsyncMock(return_value={"cpu": "200", "mem": "200G", "gpu": "20"})

        # Mock scaling group query
        sgroup_mock = MagicMock()
        sgroup_mock.name = "default"
        with patch(
            "ai.backend.manager.services.resource_preset.service.query_allowed_sgroups",
            AsyncMock(return_value=[sgroup_mock]),
        ):
            # Mock agent registry methods
            async def mock_get_keypair_occupancy(*args, **kwargs):
                return ResourceSlot({
                    "cpu": Decimal("10"),
                    "mem": Decimal("10737418240"),
                    "gpu": Decimal("1"),
                })

            async def mock_get_group_occupancy(*args, **kwargs):
                return ResourceSlot({"cpu": Decimal("5"), "mem": Decimal("5368709120")})

            async def mock_get_domain_occupancy(*args, **kwargs):
                return ResourceSlot({
                    "cpu": Decimal("20"),
                    "mem": Decimal("21474836480"),
                    "gpu": Decimal("2"),
                })

            service._agent_registry.get_keypair_occupancy = mock_get_keypair_occupancy
            service._agent_registry.get_group_occupancy = mock_get_group_occupancy
            service._agent_registry.get_domain_occupancy = mock_get_domain_occupancy

            # Mock stream queries
            async def empty_stream():
                return
                yield

            mock_conn.stream = AsyncMock(side_effect=[empty_stream(), empty_stream()])

            # Mock presets
            preset_data = ResourcePresetData(
                id=uuid.uuid4(),
                name="test-preset",
                resource_slots=ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4294967296")}),
                shared_memory=None,
                scaling_group_name=None,
            )
            deps["resource_preset_repository"].list_presets = AsyncMock(return_value=[preset_data])

    @pytest.mark.asyncio
    async def test_custom_resource_types_support(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test support for custom resource types like NPU/TPU."""
        mock_preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="custom-preset",
            resource_slots=ResourceSlot({
                "cpu": Decimal("4"),
                "mem": Decimal("8589934592"),
                "npu": Decimal("2"),
                "tpu": Decimal("1"),
            }),
            shared_memory=None,
            scaling_group_name=None,
        )

        mock_dependencies["resource_preset_repository"].create_preset_validated = AsyncMock(
            return_value=mock_preset_data
        )

        action = CreateResourcePresetAction(
            creator=ResourcePresetCreator(
                name="custom-preset",
                resource_slots=ResourceSlot({"cpu": "4", "mem": "8G", "npu": "2", "tpu": "1"}),
                shared_memory=None,
                scaling_group_name=None,
            )
        )

        result = await resource_preset_service.create_preset(action)

        assert result.resource_preset.resource_slots.data["npu"] == Decimal("2")
        assert result.resource_preset.resource_slots.data["tpu"] == Decimal("1")

    @pytest.mark.asyncio
    async def test_shared_memory_adjustment(
        self, resource_preset_service, mock_dependencies
    ) -> None:
        """Test shared memory adjustment in preset modification."""
        mock_preset_data = ResourcePresetData(
            id=uuid.uuid4(),
            name="gpu-standard",
            resource_slots=ResourceSlot({
                "cpu": Decimal("4"),
                "mem": Decimal("17179869184"),
                "gpu": Decimal("1"),
                "gpu_memory": Decimal("8589934592"),
            }),
            shared_memory=BinarySize(BinarySize.from_str("4G")),
            scaling_group_name="gpu-cluster",
        )

        mock_dependencies["resource_preset_repository"].modify_preset_validated = AsyncMock(
            return_value=mock_preset_data
        )

        action = ModifyResourcePresetAction(
            name="gpu-standard",
            id=None,
            modifier=ResourcePresetModifier(
                shared_memory=TriState.update(BinarySize(BinarySize.from_str("4G"))),
            ),
        )

        result = await resource_preset_service.modify_preset(action)

        assert result.resource_preset.shared_memory == BinarySize(BinarySize.from_str("4G"))
