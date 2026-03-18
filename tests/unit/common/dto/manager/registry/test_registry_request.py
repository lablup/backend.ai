"""Tests for registry domain request DTOs."""

import uuid

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.dto.manager.registry.request import (
    AllowedGroupsModel,
    ContainerRegistryModel,
    CreateRegistryQuotaReq,
    DeleteRegistryQuotaReq,
    HarborWebhookRequestModel,
    PatchContainerRegistryRequestModel,
    ReadRegistryQuotaReq,
    UpdateRegistryQuotaReq,
)


class TestContainerRegistryModels:
    def test_allowed_groups_model_defaults(self) -> None:
        model = AllowedGroupsModel()
        assert model.add == []
        assert model.remove == []

    def test_allowed_groups_model_with_data(self) -> None:
        model = AllowedGroupsModel(add=["group1", "group2"], remove=["group3"])
        assert model.add == ["group1", "group2"]
        assert model.remove == ["group3"]

    def test_container_registry_model_defaults(self) -> None:
        model = ContainerRegistryModel()
        assert model.id is None
        assert model.url is None
        assert model.type is None

    def test_container_registry_model_with_data(self) -> None:
        uid = uuid.uuid4()
        model = ContainerRegistryModel(
            id=uid,
            url="https://registry.example.com",
            registry_name="test-registry",
            type=ContainerRegistryType.DOCKER,
            project="myproject",
            username="user",
            password="pass",
            ssl_verify=True,
            is_global=False,
            extra={"key": "value"},
        )
        assert model.id == uid
        assert model.url == "https://registry.example.com"
        assert model.registry_name == "test-registry"

    def test_patch_container_registry_request_model(self) -> None:
        model = PatchContainerRegistryRequestModel(
            url="https://registry.example.com",
            allowed_groups=AllowedGroupsModel(add=["group1"]),
        )
        assert model.url == "https://registry.example.com"
        assert model.allowed_groups is not None
        assert model.allowed_groups.add == ["group1"]

    def test_patch_container_registry_request_model_serialization(self) -> None:
        model = PatchContainerRegistryRequestModel(
            url="https://registry.example.com",
        )
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = PatchContainerRegistryRequestModel.model_validate_json(json_data)
        assert restored.url == model.url


class TestHarborWebhookRequestModel:
    def test_harbor_webhook_model(self) -> None:
        data = {
            "type": "PUSH_ARTIFACT",
            "event_data": {
                "resources": [{"resource_url": "registry.example.com/myimage", "tag": "latest"}],
                "repository": {"namespace": "myproject", "name": "myimage"},
            },
        }
        model = HarborWebhookRequestModel.model_validate(data)
        assert model.type == "PUSH_ARTIFACT"
        assert len(model.event_data.resources) == 1
        assert model.event_data.resources[0].tag == "latest"
        assert model.event_data.repository.namespace == "myproject"
        assert model.event_data.repository.name == "myimage"


class TestRegistryQuotaModels:
    def test_create_registry_quota_req(self) -> None:
        model = CreateRegistryQuotaReq.model_validate({
            "group_id": "test-group-id",
            "quota": 100,
        })
        assert model.group_id == "test-group-id"
        assert model.quota == 100

    def test_create_registry_quota_req_group_alias(self) -> None:
        """group_id accepts 'group' as an alias."""
        model = CreateRegistryQuotaReq.model_validate({
            "group": "test-group-id",
            "quota": 100,
        })
        assert model.group_id == "test-group-id"
        assert model.quota == 100

    def test_read_registry_quota_req(self) -> None:
        model = ReadRegistryQuotaReq.model_validate({
            "group_id": "test-group-id",
        })
        assert model.group_id == "test-group-id"

    def test_read_registry_quota_req_group_alias(self) -> None:
        model = ReadRegistryQuotaReq.model_validate({
            "group": "test-group-id",
        })
        assert model.group_id == "test-group-id"

    def test_update_registry_quota_req(self) -> None:
        model = UpdateRegistryQuotaReq.model_validate({
            "group_id": "test-group-id",
            "quota": 200,
        })
        assert model.group_id == "test-group-id"
        assert model.quota == 200

    def test_update_registry_quota_req_group_alias(self) -> None:
        model = UpdateRegistryQuotaReq.model_validate({
            "group": "test-group-id",
            "quota": 200,
        })
        assert model.group_id == "test-group-id"

    def test_delete_registry_quota_req(self) -> None:
        model = DeleteRegistryQuotaReq.model_validate({
            "group_id": "test-group-id",
        })
        assert model.group_id == "test-group-id"

    def test_delete_registry_quota_req_group_alias(self) -> None:
        model = DeleteRegistryQuotaReq.model_validate({
            "group": "test-group-id",
        })
        assert model.group_id == "test-group-id"

    def test_create_registry_quota_serialization(self) -> None:
        model = CreateRegistryQuotaReq.model_validate({
            "group_id": "test-group-id",
            "quota": 100,
        })
        json_data = model.model_dump_json()
        assert isinstance(json_data, str)
        restored = CreateRegistryQuotaReq.model_validate_json(json_data)
        assert restored.group_id == model.group_id
        assert restored.quota == model.quota
