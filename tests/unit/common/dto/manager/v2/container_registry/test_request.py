"""Tests for ai.backend.common.dto.manager.v2.container_registry.request module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.container_registry.request import (
    AllowedGroupsInput,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.types import ContainerRegistryType
from ai.backend.common.exception import BackendAISchemaValidationFailed


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
            project="library",
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
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateContainerRegistryInput(
                url="",
                registry_name="my-registry",
                type=ContainerRegistryType.DOCKER,
            )

    def test_whitespace_only_url_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateContainerRegistryInput(
                url="   ",
                registry_name="my-registry",
                type=ContainerRegistryType.DOCKER,
            )

    def test_blank_registry_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateContainerRegistryInput(
                url="https://registry.example.com",
                registry_name="",
                type=ContainerRegistryType.DOCKER,
            )

    def test_whitespace_only_registry_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateContainerRegistryInput(
                url="https://registry.example.com",
                registry_name="   ",
                type=ContainerRegistryType.DOCKER,
            )

    def test_missing_url_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateContainerRegistryInput.model_validate({
                "registry_name": "my-registry",
                "type": "docker",
            })

    def test_missing_registry_name_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateContainerRegistryInput.model_validate({
                "url": "https://registry.example.com",
                "type": "docker",
            })

    def test_missing_type_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateContainerRegistryInput.model_validate({
                "url": "https://registry.example.com",
                "registry_name": "my-registry",
            })


@dataclass(frozen=True)
class _RejectedProjectCase:
    project: str
    message: str


class TestCreateContainerRegistryInputRegistryRules:
    """Tests for the URL and Harbor project rules on CreateContainerRegistryInput."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://registry.example.com/v2",
            "192.168.1.100:5000",
            "localhost",
            "registry.local",
            "example.com:8080",
        ],
    )
    def test_url_accepted(self, url: str) -> None:
        req = CreateContainerRegistryInput(
            url=url,
            registry_name="my-registry",
            type=ContainerRegistryType.DOCKER,
        )
        assert req.url == url

    @pytest.mark.parametrize("url", ["http://", "https://"])
    def test_url_without_host_rejected(self, url: str) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match=f"Invalid URL format: {url}"):
            CreateContainerRegistryInput.model_validate({
                "url": url,
                "registry_name": "my-registry",
                "type": "docker",
            })

    @pytest.mark.parametrize(
        "registry_type",
        [ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2],
        ids=lambda registry_type: registry_type.value,
    )
    def test_harbor_without_project_rejected(self, registry_type: ContainerRegistryType) -> None:
        with pytest.raises(
            BackendAISchemaValidationFailed, match=r"Project name is required for Harbor\."
        ):
            CreateContainerRegistryInput.model_validate({
                "url": "https://harbor.example.com",
                "registry_name": "harbor-registry",
                "type": registry_type.value,
            })

    @pytest.mark.parametrize(
        "registry_type",
        [
            ContainerRegistryType.DOCKER,
            ContainerRegistryType.GITHUB,
            ContainerRegistryType.GITLAB,
            ContainerRegistryType.ECR,
            ContainerRegistryType.ECR_PUB,
            ContainerRegistryType.LOCAL,
            ContainerRegistryType.OCP,
        ],
        ids=lambda registry_type: registry_type.value,
    )
    def test_non_harbor_without_project_accepted(
        self, registry_type: ContainerRegistryType
    ) -> None:
        req = CreateContainerRegistryInput(
            url="https://registry.example.com",
            registry_name="my-registry",
            type=registry_type,
        )
        assert req.project is None

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedProjectCase(project="", message="Invalid project name length."),
            _RejectedProjectCase(project="a" * 256, message="Invalid project name length."),
            _RejectedProjectCase(project="-project", message="Invalid project name format."),
            _RejectedProjectCase(project="project.", message="Invalid project name format."),
            _RejectedProjectCase(project="Project", message="Invalid project name format."),
            _RejectedProjectCase(project="project name", message="Invalid project name format."),
            _RejectedProjectCase(project="project--name", message="Invalid project name format."),
        ],
        ids=lambda case: case.project[:12] or "empty",
    )
    def test_harbor_project_rejected(self, case: _RejectedProjectCase) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match=case.message):
            CreateContainerRegistryInput.model_validate({
                "url": "https://harbor.example.com",
                "registry_name": "harbor-registry",
                "type": "harbor",
                "project": case.project,
            })

    @pytest.mark.parametrize(
        "project",
        ["p", "project1", "my-project", "my_project", "my.project", "project-name_test", "a" * 255],
    )
    def test_harbor_project_accepted(self, project: str) -> None:
        req = CreateContainerRegistryInput(
            url="https://harbor.example.com",
            registry_name="harbor-registry",
            type=ContainerRegistryType.HARBOR,
            project=project,
        )
        assert req.project == project


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


class TestUpdateContainerRegistryInputRegistryRules:
    """Tests for the URL and Harbor project rules on UpdateContainerRegistryInput."""

    @pytest.mark.parametrize("url", ["http://", "https://"])
    def test_url_without_host_rejected(self, url: str) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match=f"Invalid URL format: {url}"):
            UpdateContainerRegistryInput.model_validate({"id": str(uuid.uuid4()), "url": url})

    @pytest.mark.parametrize(
        "registry_type",
        [ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2],
        ids=lambda registry_type: registry_type.value,
    )
    def test_harbor_type_without_project_accepted(
        self, registry_type: ContainerRegistryType
    ) -> None:
        req = UpdateContainerRegistryInput(id=uuid.uuid4(), type=registry_type)
        assert req.project is None

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedProjectCase(project="", message="Invalid project name length."),
            _RejectedProjectCase(project="a" * 256, message="Invalid project name length."),
            _RejectedProjectCase(project="Project", message="Invalid project name format."),
            _RejectedProjectCase(project="project--name", message="Invalid project name format."),
        ],
        ids=lambda case: case.project[:12] or "empty",
    )
    def test_harbor_type_with_project_rejected(self, case: _RejectedProjectCase) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match=case.message):
            UpdateContainerRegistryInput.model_validate({
                "id": str(uuid.uuid4()),
                "type": "harbor",
                "project": case.project,
            })

    def test_project_without_type_accepted(self) -> None:
        req = UpdateContainerRegistryInput(id=uuid.uuid4(), project="Project")
        assert req.project == "Project"


class TestUpdateContainerRegistryInputValidationFailures:
    """Tests for UpdateContainerRegistryInput validation failures."""

    def test_blank_url_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateContainerRegistryInput(id=reg_id, url="")

    def test_whitespace_only_url_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateContainerRegistryInput(id=reg_id, url="   ")

    def test_blank_registry_name_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateContainerRegistryInput(id=reg_id, registry_name="")

    def test_whitespace_only_registry_name_raises_validation_error(self) -> None:
        reg_id = uuid.uuid4()
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateContainerRegistryInput(id=reg_id, registry_name="   ")

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
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
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DeleteContainerRegistryInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
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
