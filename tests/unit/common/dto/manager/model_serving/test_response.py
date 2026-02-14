import uuid

from pydantic import HttpUrl

from ai.backend.common.dto.manager.model_serving.response import (
    CompactServeInfoModel,
    ErrorInfoModel,
    ErrorListResponseModel,
    PaginationInfoModel,
    RouteInfoModel,
    RuntimeInfo,
    RuntimeInfoModel,
    ScaleResponseModel,
    SearchServicesResponseModel,
    ServeInfoModel,
    ServiceSearchItemModel,
    SuccessResponseModel,
    TokenResponseModel,
    TryStartResponseModel,
)
from ai.backend.common.types import RuntimeVariant


class TestSuccessResponseModel:
    def test_default_success(self) -> None:
        model = SuccessResponseModel()
        assert model.success is True

    def test_explicit_false(self) -> None:
        model = SuccessResponseModel(success=False)
        assert model.success is False

    def test_serialization(self) -> None:
        model = SuccessResponseModel()
        data = model.model_dump()
        assert data["success"] is True


class TestCompactServeInfoModel:
    def test_construction(self) -> None:
        eid = uuid.uuid4()
        model = CompactServeInfoModel(
            id=eid,
            name="my-service",
            replicas=3,
            desired_session_count=3,
            active_route_count=2,
            service_endpoint=HttpUrl("https://example.com/api"),
            is_public=False,
        )
        assert model.id == eid
        assert model.name == "my-service"
        assert model.replicas == 3
        assert model.desired_session_count == 3
        assert model.active_route_count == 2
        assert model.service_endpoint is not None
        assert model.is_public is False

    def test_nullable_endpoint(self) -> None:
        model = CompactServeInfoModel(
            id=uuid.uuid4(),
            name="svc",
            replicas=1,
            desired_session_count=1,
            active_route_count=0,
            is_public=True,
        )
        assert model.service_endpoint is None


class TestRouteInfoModel:
    def test_construction(self) -> None:
        rid = uuid.uuid4()
        sid = uuid.uuid4()
        model = RouteInfoModel(route_id=rid, session_id=sid, traffic_ratio=0.75)
        assert model.route_id == rid
        assert model.session_id == sid
        assert model.traffic_ratio == 0.75

    def test_null_session(self) -> None:
        model = RouteInfoModel(route_id=uuid.uuid4(), session_id=None, traffic_ratio=1.0)
        assert model.session_id is None


class TestServeInfoModel:
    def test_field_completeness(self) -> None:
        eid = uuid.uuid4()
        mid = uuid.uuid4()
        rid = uuid.uuid4()
        model = ServeInfoModel(
            endpoint_id=eid,
            model_id=mid,
            extra_mounts=[uuid.uuid4()],
            name="test-serve",
            replicas=2,
            desired_session_count=2,
            model_definition_path="model-definition.yaml",
            active_routes=[
                RouteInfoModel(route_id=rid, session_id=uuid.uuid4(), traffic_ratio=1.0)
            ],
            service_endpoint=HttpUrl("https://serve.example.com"),
            is_public=False,
            runtime_variant=RuntimeVariant.CUSTOM,
        )
        assert model.endpoint_id == eid
        assert model.model_id == mid
        assert len(model.extra_mounts) == 1
        assert model.name == "test-serve"
        assert model.replicas == 2
        assert model.model_definition_path == "model-definition.yaml"
        assert len(model.active_routes) == 1
        assert model.runtime_variant == RuntimeVariant.CUSTOM

    def test_nullable_fields(self) -> None:
        model = ServeInfoModel(
            endpoint_id=uuid.uuid4(),
            model_id=uuid.uuid4(),
            extra_mounts=[],
            name="svc",
            replicas=0,
            desired_session_count=0,
            model_definition_path=None,
            active_routes=[],
            is_public=True,
            runtime_variant=RuntimeVariant.CUSTOM,
        )
        assert model.service_endpoint is None
        assert model.model_definition_path is None

    def test_serialization_roundtrip(self) -> None:
        model = ServeInfoModel(
            endpoint_id=uuid.uuid4(),
            model_id=uuid.uuid4(),
            extra_mounts=[],
            name="svc",
            replicas=1,
            desired_session_count=1,
            model_definition_path=None,
            active_routes=[],
            is_public=False,
            runtime_variant=RuntimeVariant.CUSTOM,
        )
        data = model.model_dump()
        assert data["name"] == "svc"
        assert data["replicas"] == 1


class TestSearchServicesResponseModel:
    def test_with_items_and_pagination(self) -> None:
        model = SearchServicesResponseModel(
            items=[
                ServiceSearchItemModel(
                    id=uuid.uuid4(),
                    name="svc-1",
                    desired_session_count=1,
                    replicas=1,
                    active_route_count=1,
                    resource_slots={"cpu": "4"},
                    resource_group="default",
                    open_to_public=False,
                ),
            ],
            pagination=PaginationInfoModel(total=1, offset=0, limit=20),
        )
        assert len(model.items) == 1
        assert model.pagination.total == 1
        assert model.pagination.offset == 0
        assert model.pagination.limit == 20

    def test_empty_results(self) -> None:
        model = SearchServicesResponseModel(
            items=[],
            pagination=PaginationInfoModel(total=0, offset=0, limit=20),
        )
        assert len(model.items) == 0
        assert model.pagination.total == 0


class TestTryStartResponseModel:
    def test_construction(self) -> None:
        model = TryStartResponseModel(task_id="abc-123")
        assert model.task_id == "abc-123"


class TestScaleResponseModel:
    def test_serialization(self) -> None:
        model = ScaleResponseModel(current_route_count=2, target_count=5)
        data = model.model_dump()
        assert data["current_route_count"] == 2
        assert data["target_count"] == 5


class TestTokenResponseModel:
    def test_serialization(self) -> None:
        model = TokenResponseModel(token="eyJhbGciOiJIUzI1NiJ9.test.signature")
        data = model.model_dump()
        assert data["token"] == "eyJhbGciOiJIUzI1NiJ9.test.signature"


class TestErrorListResponseModel:
    def test_with_errors(self) -> None:
        sid = uuid.uuid4()
        model = ErrorListResponseModel(
            errors=[
                ErrorInfoModel(
                    session_id=sid,
                    error={"type": "InternalError", "message": "OOM"},
                ),
                ErrorInfoModel(
                    session_id=None,
                    error={"type": "SchedulingError", "message": "No resources"},
                ),
            ],
            retries=3,
        )
        assert len(model.errors) == 2
        assert model.errors[0].session_id == sid
        assert model.errors[1].session_id is None
        assert model.retries == 3

    def test_empty_errors(self) -> None:
        model = ErrorListResponseModel(errors=[], retries=0)
        assert len(model.errors) == 0
        assert model.retries == 0


class TestRuntimeInfoModel:
    def test_with_runtimes(self) -> None:
        model = RuntimeInfoModel(
            runtimes=[
                RuntimeInfo(name="custom", human_readable_name="Custom Runtime"),
                RuntimeInfo(name="vllm", human_readable_name="vLLM"),
            ],
        )
        assert len(model.runtimes) == 2
        assert model.runtimes[0].name == "custom"
        assert model.runtimes[1].human_readable_name == "vLLM"

    def test_empty_runtimes(self) -> None:
        model = RuntimeInfoModel(runtimes=[])
        assert len(model.runtimes) == 0

    def test_serialization(self) -> None:
        model = RuntimeInfoModel(
            runtimes=[
                RuntimeInfo(name="custom", human_readable_name="Custom"),
            ],
        )
        data = model.model_dump()
        assert len(data["runtimes"]) == 1
        assert data["runtimes"][0]["name"] == "custom"
