from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import SlotName
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.etcd_config import EtcdConfigRepository
from ai.backend.manager.services.etcd_config.actions.delete_config import DeleteConfigAction
from ai.backend.manager.services.etcd_config.actions.get_config import GetConfigAction
from ai.backend.manager.services.etcd_config.actions.get_resource_metadata import (
    GetResourceMetadataAction,
)
from ai.backend.manager.services.etcd_config.actions.get_resource_slots import (
    GetResourceSlotsAction,
)
from ai.backend.manager.services.etcd_config.actions.get_vfolder_types import (
    GetVfolderTypesAction,
)
from ai.backend.manager.services.etcd_config.actions.set_config import SetConfigAction
from ai.backend.manager.services.etcd_config.service import EtcdConfigService


class TestEtcdConfigService:
    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        return AsyncMock(spec=EtcdConfigRepository)

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        provider = MagicMock(spec=ManagerConfigProvider)
        provider.legacy_etcd_config_loader = MagicMock()
        return provider

    @pytest.fixture
    def mock_etcd(self) -> AsyncMock:
        return AsyncMock(spec=AsyncEtcd)

    @pytest.fixture
    def mock_valkey_stat(self) -> AsyncMock:
        return AsyncMock(spec=ValkeyStatClient)

    @pytest.fixture
    def service(
        self,
        mock_repository: AsyncMock,
        mock_config_provider: MagicMock,
        mock_etcd: AsyncMock,
        mock_valkey_stat: AsyncMock,
    ) -> EtcdConfigService:
        return EtcdConfigService(
            repository=mock_repository,
            config_provider=mock_config_provider,
            etcd=mock_etcd,
            valkey_stat=mock_valkey_stat,
        )


class TestGetConfig(TestEtcdConfigService):
    async def test_prefix_false_returns_scalar_value(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get.return_value = "some_value"
        action = GetConfigAction(key="config/key", prefix=False)

        result = await service.get_config(action)

        assert result.result == "some_value"
        mock_etcd.get.assert_called_once_with("config/key")

    async def test_prefix_true_returns_nested_dict(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get_prefix_dict.return_value = {"sub1": "val1", "sub2": "val2"}
        action = GetConfigAction(key="config/", prefix=True)

        result = await service.get_config(action)

        assert result.result == {"sub1": "val1", "sub2": "val2"}
        mock_etcd.get_prefix_dict.assert_called_once_with("config/")

    async def test_non_existent_key_returns_none(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get.return_value = None
        action = GetConfigAction(key="nonexistent/key", prefix=False)

        result = await service.get_config(action)

        assert result.result is None

    async def test_prefix_with_no_match_returns_empty_dict(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.get_prefix_dict.return_value = {}
        action = GetConfigAction(key="empty/prefix/", prefix=True)

        result = await service.get_config(action)

        assert result.result == {}


class TestSetConfig(TestEtcdConfigService):
    async def test_scalar_value_calls_etcd_put(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        action = SetConfigAction(key="config/key", value="scalar_value")

        await service.set_config(action)

        mock_etcd.put.assert_called_once_with("config/key", "scalar_value")

    async def test_dict_value_calls_put_dict(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        action = SetConfigAction(key="config/key", value={"sub": "val"})

        await service.set_config(action)

        mock_etcd.put_dict.assert_called_once_with({"config/key/sub": "val"})

    async def test_too_many_flattened_pairs_raises_invalid_api_parameters(
        self,
        service: EtcdConfigService,
    ) -> None:
        large_dict = {f"key{i}": f"val{i}" for i in range(17)}
        action = SetConfigAction(key="config", value=large_dict)

        with pytest.raises(InvalidAPIParameters):
            await service.set_config(action)

    async def test_nested_dict_flattens_with_slash_separator(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        action = SetConfigAction(
            key="root",
            value={"level1": {"level2": {"level3": "deep_value"}}},
        )

        await service.set_config(action)

        mock_etcd.put_dict.assert_called_once_with({"root/level1/level2/level3": "deep_value"})


class TestDeleteConfig(TestEtcdConfigService):
    async def test_prefix_false_calls_etcd_delete(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        action = DeleteConfigAction(key="config/key", prefix=False)

        await service.delete_config(action)

        mock_etcd.delete.assert_called_once_with("config/key")

    async def test_prefix_true_calls_etcd_delete_prefix(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        action = DeleteConfigAction(key="config/prefix/", prefix=True)

        await service.delete_config(action)

        mock_etcd.delete_prefix.assert_called_once_with("config/prefix/")

    async def test_deleting_non_existent_key_is_idempotent(
        self,
        service: EtcdConfigService,
        mock_etcd: AsyncMock,
    ) -> None:
        mock_etcd.delete.return_value = None
        action = DeleteConfigAction(key="nonexistent/key", prefix=False)

        result = await service.delete_config(action)

        assert result is not None


class TestGetResourceSlots(TestEtcdConfigService):
    async def test_returns_known_slots(
        self,
        service: EtcdConfigService,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value={
                SlotName("cpu"): "count",
                SlotName("mem"): "bytes",
                SlotName("cuda.device"): "count",
            }
        )
        action = GetResourceSlotsAction()

        result = await service.get_resource_slots(action)

        assert "cpu" in result.slots
        assert "mem" in result.slots
        assert "cuda.device" in result.slots


class TestGetResourceMetadata(TestEtcdConfigService):
    async def test_sgroup_none_returns_all_metadata(
        self,
        service: EtcdConfigService,
        mock_config_provider: MagicMock,
        mock_valkey_stat: AsyncMock,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value={
                SlotName("cpu"): "count",
                SlotName("mem"): "bytes",
            }
        )
        mock_valkey_stat.get_computer_metadata.return_value = {}
        action = GetResourceMetadataAction(sgroup=None)

        result = await service.get_resource_metadata(action)

        assert "cpu" in result.metadata
        assert "mem" in result.metadata

    async def test_specific_sgroup_filters_by_agent_slots(
        self,
        service: EtcdConfigService,
        mock_config_provider: MagicMock,
        mock_valkey_stat: AsyncMock,
        mock_repository: AsyncMock,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value={
                SlotName("cpu"): "count",
                SlotName("mem"): "bytes",
                SlotName("cuda.device"): "count",
            }
        )
        mock_valkey_stat.get_computer_metadata.return_value = {}
        mock_repository.get_available_agent_slots.return_value = {"cuda.device"}
        action = GetResourceMetadataAction(sgroup="test-group")

        result = await service.get_resource_metadata(action)

        assert "cpu" in result.metadata
        assert "mem" in result.metadata
        assert "cuda.device" in result.metadata
        mock_repository.get_available_agent_slots.assert_called_once_with("test-group")

    async def test_reported_accelerator_metadata_merges_with_known(
        self,
        service: EtcdConfigService,
        mock_config_provider: MagicMock,
        mock_valkey_stat: AsyncMock,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value={
                SlotName("cpu"): "count",
                SlotName("custom.accelerator"): "count",
            }
        )
        custom_metadata = {
            "slot_name": "custom.accelerator",
            "human_readable_name": "Custom Accel",
            "description": "A custom accelerator",
            "display_unit": "Device",
            "number_format": {"binary": False, "round_length": 0},
            "display_icon": "custom",
        }
        mock_valkey_stat.get_computer_metadata.return_value = {
            "custom.accelerator": json.dumps(custom_metadata).encode(),
        }
        action = GetResourceMetadataAction(sgroup=None)

        result = await service.get_resource_metadata(action)

        assert "custom.accelerator" in result.metadata
        assert result.metadata["custom.accelerator"]["human_readable_name"] == "Custom Accel"
        assert "cpu" in result.metadata


class TestGetVfolderTypes(TestEtcdConfigService):
    async def test_returns_configured_vfolder_types(
        self,
        service: EtcdConfigService,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(
            return_value=["user", "group"]
        )
        action = GetVfolderTypesAction()

        result = await service.get_vfolder_types(action)

        assert result.types == ["user", "group"]

    async def test_unconfigured_returns_empty_list(
        self,
        service: EtcdConfigService,
        mock_config_provider: MagicMock,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(
            return_value=[]
        )
        action = GetVfolderTypesAction()

        result = await service.get_vfolder_types(action)

        assert result.types == []
