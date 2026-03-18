import time

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.model_serving.request import (
    ListServeRequestModel,
    NewServiceRequestModel,
    ScaleRequestModel,
    SearchServicesRequestModel,
    ServiceConfigModel,
    ServiceFilterModel,
    TokenRequestModel,
    UpdateRouteRequestModel,
)


class TestListServeRequestModel:
    def test_default_name_is_none(self) -> None:
        model = ListServeRequestModel()
        assert model.name is None

    def test_with_name(self) -> None:
        model = ListServeRequestModel(name="my-service")
        assert model.name == "my-service"


class TestServiceFilterModel:
    def test_default_filter_is_none(self) -> None:
        model = ServiceFilterModel()
        assert model.name is None

    def test_with_string_filter(self) -> None:
        model = ServiceFilterModel.model_validate({"name": {"contains": "test"}})
        assert model.name is not None
        assert model.name.contains == "test"


class TestSearchServicesRequestModel:
    def test_defaults(self) -> None:
        model = SearchServicesRequestModel()
        assert model.filter is None
        assert model.offset == 0
        assert model.limit == 20

    def test_with_filter_and_pagination(self) -> None:
        model = SearchServicesRequestModel.model_validate({
            "filter": {"name": {"contains": "llm"}},
            "offset": 10,
            "limit": 50,
        })
        assert model.filter is not None
        assert model.filter.name is not None
        assert model.filter.name.contains == "llm"
        assert model.offset == 10
        assert model.limit == 50

    def test_offset_must_be_non_negative(self) -> None:
        with pytest.raises(ValidationError):
            SearchServicesRequestModel(offset=-1)

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            SearchServicesRequestModel(limit=0)
        with pytest.raises(ValidationError):
            SearchServicesRequestModel(limit=101)


class TestServiceConfigModel:
    def test_minimal_config(self) -> None:
        model = ServiceConfigModel(
            model="ResNet50",
            scaling_group="nvidia-H100",
        )
        assert model.model == "ResNet50"
        assert model.scaling_group == "nvidia-H100"
        assert model.model_version == 1
        assert model.model_mount_destination == "/models"
        assert model.extra_mounts == {}
        assert model.environ is None
        assert model.resources is None
        assert model.resource_opts == {}

    def test_alias_resolution(self) -> None:
        model = ServiceConfigModel.model_validate({
            "model": "test-model",
            "scalingGroup": "my-group",
            "modelVersion": 2,
            "modelMountDestination": "/custom/path",
        })
        assert model.scaling_group == "my-group"
        assert model.model_version == 2
        assert model.model_mount_destination == "/custom/path"

    def test_with_resources(self) -> None:
        model = ServiceConfigModel(
            model="test-model",
            scaling_group="default",
            resources={"cpu": 4, "mem": "32g"},
            resource_opts={"shmem": "2g"},
        )
        assert model.resources == {"cpu": 4, "mem": "32g"}
        assert model.resource_opts == {"shmem": "2g"}


class TestNewServiceRequestModel:
    def test_minimal_creation(self) -> None:
        model = NewServiceRequestModel.model_validate({
            "name": "test-service",
            "desired_session_count": 2,
            "config": {
                "model": "ResNet50",
                "scalingGroup": "default",
            },
        })
        assert model.service_name == "test-service"
        assert model.replicas == 2
        assert model.image is None
        assert model.group_name == "default"
        assert model.domain_name == "default"
        assert model.open_to_public is False

    def test_camel_case_aliases(self) -> None:
        model = NewServiceRequestModel.model_validate({
            "name": "test-service",
            "desiredSessionCount": 3,
            "config": {
                "model": "test-model",
                "scalingGroup": "gpu-group",
            },
            "clusterSize": 2,
            "clusterMode": "MULTI_NODE",
            "startupCommand": "python serve.py",
            "bootstrapScript": "pip install deps",
        })
        assert model.replicas == 3
        assert model.cluster_size == 2
        assert model.cluster_mode == "MULTI_NODE"
        assert model.startup_command == "python serve.py"
        assert model.bootstrap_script == "pip install deps"

    def test_service_name_pattern_validation(self) -> None:
        with pytest.raises(ValidationError):
            NewServiceRequestModel.model_validate({
                "name": "ab",  # too short (min_length=4)
                "desired_session_count": 1,
                "config": {
                    "model": "test-model",
                    "scalingGroup": "default",
                },
            })

    def test_full_creation(self) -> None:
        model = NewServiceRequestModel.model_validate({
            "name": "my-llm-service",
            "desired_session_count": 1,
            "lang": "cr.backend.ai/stable/python:3.11",
            "arch": "aarch64",
            "group": "research",
            "domain": "example.com",
            "tag": "v1.0",
            "open_to_public": True,
            "config": {
                "model": "my-model",
                "scalingGroup": "gpu-pool",
                "resources": {"cpu": 4, "mem": "16g"},
            },
        })
        assert model.image == "cr.backend.ai/stable/python:3.11"
        assert model.architecture == "aarch64"
        assert model.group_name == "research"
        assert model.domain_name == "example.com"
        assert model.tag == "v1.0"
        assert model.open_to_public is True


class TestScaleRequestModel:
    def test_scale_to(self) -> None:
        model = ScaleRequestModel(to=5)
        assert model.to == 5


class TestUpdateRouteRequestModel:
    def test_traffic_ratio(self) -> None:
        model = UpdateRouteRequestModel(traffic_ratio=0.5)
        assert model.traffic_ratio == 0.5

    def test_zero_traffic_ratio(self) -> None:
        model = UpdateRouteRequestModel(traffic_ratio=0.0)
        assert model.traffic_ratio == 0.0

    def test_negative_traffic_ratio_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UpdateRouteRequestModel(traffic_ratio=-0.1)


class TestTokenRequestModel:
    def test_with_valid_until(self) -> None:
        future_ts = int(time.time()) + 3600
        model = TokenRequestModel(valid_until=future_ts)
        assert model.expires_at == future_ts

    def test_with_duration(self) -> None:
        model = TokenRequestModel.model_validate({"duration": "1h"})
        assert model.expires_at > int(time.time())

    def test_neither_raises_error(self) -> None:
        with pytest.raises(ValidationError, match="Either valid_until or duration"):
            TokenRequestModel()

    def test_past_expiration_raises_error(self) -> None:
        past_ts = int(time.time()) - 3600
        with pytest.raises(ValidationError, match="cannot be in the past"):
            TokenRequestModel(valid_until=past_ts)

    def test_roundtrip(self) -> None:
        future_ts = int(time.time()) + 7200
        model = TokenRequestModel(valid_until=future_ts)
        data = model.model_dump()
        restored = TokenRequestModel(valid_until=data["valid_until"])
        assert restored.expires_at == model.expires_at
