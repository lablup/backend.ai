"""Tests for ai.backend.common.dto.manager.v2.container_registry.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.container_registry.request import (
    AllowedGroupsInput,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.types import ContainerRegistryType


class TestAllowedGroupsInput:
    """Tests for AllowedGroupsInput model."""

    def test_defaults_are_empty_lists(self) -> None:
        inp = AllowedGroupsInput()
        assert inp.add == []
        assert inp.remove == []

    def test_with_add_groups(self) -> None:
        inp = AllowedGroupsInput(add=["group-1", "group-2"])
        assert inp.add == ["group-1", "group-2"]
        assert inp.remove == []

    def test_with_remove_groups(self) -> None:
        inp = AllowedGroupsInput(remove=["group-3"])
        assert inp.add == []
        assert inp.remove == ["group-3"]

    def test_with_both(self) -> None:
        inp = AllowedGroupsInput(add=["g1"], remove=["g2"])
        assert inp.add == ["g1"]
        assert inp.remove == ["g2"]

    def test_round_trip_serialization(self) -> None:
        inp = AllowedGroupsInput(add=["admin"], remove=["user"])
        json_str = inp.model_dump_json()
        restored = AllowedGroupsInput.model_validate_json(json_str)
        assert restored.add == ["admin"]
        assert restored.remove == ["user"]


class TestCreateContainerRegistryInput:
    """Tests for CreateContainerRegistryInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = CreateContainerRegistryInput(
            url="https://registry.example.com",
            registry_name="my-registry",
            type=ContainerRegistryType.DOCKER,
        )
        assert req.url == "https://registry.example.com"
        assert req.registry_name == "my-registry"
        assert req.type == ContainerRegistryType.DOCKER

    def test_optional_fields_default_to_none(self) -> None:
        req = CreateContainerRegistryInput(
            url="https://registry.example.com",
            registry_name="my-registry",
            type=ContainerRegistryType.DOCKER,
        )
        assert req.project is None
        assert req.username is None
        assert req.password is None
        assert req.ssl_verify is None
        assert req.is_global is None
        assert req.extra is None
        assert req.allowed_groups is None

    def test_with_all_optional_fields(self) -> None:
        req = CreateContainerRegistryInput(
            url="https://registry.example.com",
            registry_name="my-registry",
            type=ContainerRegistryType.HARBOR,
            project="myproject",
            username="admin",
            password="secret",
            ssl_verify=True,
            is_global=False,
        )
        assert req.project == "myproject"
        assert req.username == "admin"
        assert req.password == "secret"
        assert req.ssl_verify is True
        assert req.is_global is False

    def test_url_whitespace_stripped(self) -> None:
        req = CreateContainerRegistryInput(
            url="  https://registry.example.com  ",
            registry_name="my-registry",
            type=ContainerRegistryType.DOCKER,
        )
        assert req.url == "https://registry.example.com"

    def test_registry_name_whitespace_stripped(self) -> None:
        req = CreateContainerRegistryInput(
            url="https://registry.example.com",
            registry_name="  my-registry  ",
            type=ContainerRegistryType.DOCKER,
        )
        assert req.registry_name == "my-registry"

    def test_harbor2_type(self) -> None:
        req = CreateContainerRegistryInput(
            url="https://harbor.example.com",
            registry_name="harbor-registry",
            type=ContainerRegistryType.HARBOR2,
        )
        assert req.type == ContainerRegistryType.HARBOR2

    def test_round_trip_serialization(self) -> None:
        req = CreateContainerRegistryInput(
            url="https://registry.example.com",
            registry_name="test-reg",
            type=ContainerRegistryType.GITHUB,
        )
        json_str = req.model_dump_json()
        restored = CreateContainerRegistryInput.model_validate_json(json_str)
        assert restored.url == req.url
        assert restored.registry_name == req.registry_name
        assert restored.type == ContainerRegistryType.GITHUB


class TestCreateContainerRegistryInputValidationFailures:
    """Tests for CreateContainerRegistryInput validation failures."""

    def test_blank_url_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateContainerRegistryInput(
                url="",
                registry_name="my-registry",
                type=ContainerRegistryType.DOCKER,
            )

    def test_whitespace_only_url_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateContainerRegistryInput(
                url="   ",
                registry_name="my-registry",
                type=ContainerRegistryType.DOCKER,
            )

    def test_blank_registry_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateContainerRegistryInput(
                url="https://registry.example.com",
                registry_name="",
                type=ContainerRegistryType.DOCKER,
            )

    def test_whitespace_only_registry_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateContainerRegistryInput(
                url="https://registry.example.com",
                registry_name="   ",
                type=ContainerRegistryType.DOCKER,
            )

    def test_missing_url_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateContainerRegistryInput.model_validate({
                "registry_name": "my-registry",
                "type": "docker",
            })

    def test_missing_registry_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateContainerRegistryInput.model_validate({
                "url": "https://registry.example.com",
                "type": "docker",
            })

    def test_missing_type_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateContainerRegistryInput.model_validate({
                "url": "https://registry.example.com",
                "registry_name": "my-registry",
            })


class TestUpdateContainerRegistryInput:
    """Tests for UpdateContainerRegistryInput model creation and validation."""

    def test_valid_creation_with_id_only(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(id=reg_id)
        assert req.id == reg_id
        assert req.url is None
        assert req.registry_name is None
        assert req.type is None

    def test_update_url(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(id=reg_id, url="https://new-registry.example.com")
        assert req.url == "https://new-registry.example.com"

    def test_update_registry_name(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(id=reg_id, registry_name="new-registry")
        assert req.registry_name == "new-registry"

    def test_update_type(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(id=reg_id, type=ContainerRegistryType.HARBOR)
        assert req.type == ContainerRegistryType.HARBOR

    def test_url_whitespace_stripped(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(id=reg_id, url="  https://registry.example.com  ")
        assert req.url == "https://registry.example.com"

    def test_registry_name_whitespace_stripped(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(id=reg_id, registry_name="  updated-registry  ")
        assert req.registry_name == "updated-registry"

    def test_none_url_means_no_change(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(id=reg_id, url=None)
        assert req.url is None

    def test_round_trip_serialization(self) -> None:
        reg_id = uuid.uuid4()
        req = UpdateContainerRegistryInput(
            id=reg_id,
            url="https://updated.example.com",
            type=ContainerRegistryType.GITLAB,
        )
        json_str = req.model_dump_json()
        restored = UpdateContainerRegistryInput.model_validate_json(json_str)
        assert restored.id == reg_id
        assert restored.url == "https://updated.example.com"
        assert restored.type == ContainerRegistryType.GITLAB


class TestUpdateContainerRegistryInputValidationFailures:
    """Tests for UpdateContainerRegistryInput validation failures."""

    def test_blank_url_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            UpdateContainerRegistryInput(id=reg_id, url="")

    def test_whitespace_only_url_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            UpdateContainerRegistryInput(id=reg_id, url="   ")

    def test_blank_registry_name_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            UpdateContainerRegistryInput(id=reg_id, registry_name="")

    def test_whitespace_only_registry_name_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            UpdateContainerRegistryInput(id=reg_id, registry_name="   ")

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateContainerRegistryInput.model_validate({})


class TestDeleteContainerRegistryInput:
    """Tests for DeleteContainerRegistryInput model creation and validation."""

    def test_valid_creation_with_uuid(self) -> None:
        reg_id = uuid.uuid4()
        req = DeleteContainerRegistryInput(id=reg_id)
        assert req.id == reg_id

    def test_valid_creation_from_uuid_string(self) -> None:
        reg_id = uuid.uuid4()
        req = DeleteContainerRegistryInput.model_validate({"id": str(reg_id)})
        assert req.id == reg_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteContainerRegistryInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteContainerRegistryInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        reg_id = uuid.uuid4()
        req = DeleteContainerRegistryInput(id=reg_id)
        assert isinstance(req.id, uuid.UUID)

    def test_round_trip_serialization(self) -> None:
        reg_id = uuid.uuid4()
        req = DeleteContainerRegistryInput(id=reg_id)
        json_str = req.model_dump_json()
        restored = DeleteContainerRegistryInput.model_validate_json(json_str)
        assert restored.id == reg_id
