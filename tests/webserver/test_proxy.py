from __future__ import annotations

from ai.backend.web.proxy import (
    _transform_downstream_service_errors,
)


class TestTransformDownstreamServiceErrors:
    def test_no_errors_key(self) -> None:
        data: dict = {"data": {"user": {"id": "1"}}}
        result = _transform_downstream_service_errors(data)
        assert result == data

    def test_empty_errors_list(self) -> None:
        data: dict = {"data": None, "errors": []}
        result = _transform_downstream_service_errors(data)
        assert result == data

    def test_errors_is_none(self) -> None:
        data: dict = {"data": None, "errors": None}
        result = _transform_downstream_service_errors(data)
        assert result == data

    def test_replaces_downstream_service_error(self) -> None:
        data: dict = {
            "data": None,
            "errors": [
                {
                    "message": "Resource not found.",
                    "extensions": {
                        "code": "DOWNSTREAM_SERVICE_ERROR",
                        "serviceName": "graphene",
                    },
                }
            ],
        }
        result = _transform_downstream_service_errors(data)
        error = result["errors"][0]
        assert error["extensions"]["code"] == "backendai_generic_internal-error"
        assert "serviceName" not in error["extensions"]
        assert error["message"] == "Resource not found."

    def test_preserves_non_downstream_error(self) -> None:
        data: dict = {
            "data": None,
            "errors": [
                {
                    "message": "Forbidden",
                    "extensions": {
                        "code": "api_auth_forbidden",
                    },
                }
            ],
        }
        result = _transform_downstream_service_errors(data)
        assert result["errors"][0]["extensions"]["code"] == "api_auth_forbidden"

    def test_handles_multiple_errors(self) -> None:
        data: dict = {
            "data": None,
            "errors": [
                {
                    "message": "Error one",
                    "extensions": {
                        "code": "DOWNSTREAM_SERVICE_ERROR",
                        "serviceName": "graphene",
                    },
                },
                {
                    "message": "Error two",
                    "extensions": {
                        "code": "backendai_read_not-found",
                    },
                },
                {
                    "message": "Error three",
                    "extensions": {
                        "code": "DOWNSTREAM_SERVICE_ERROR",
                        "serviceName": "strawberry",
                    },
                },
            ],
        }
        result = _transform_downstream_service_errors(data)
        assert result["errors"][0]["extensions"]["code"] == "backendai_generic_internal-error"
        assert "serviceName" not in result["errors"][0]["extensions"]
        assert result["errors"][1]["extensions"]["code"] == "backendai_read_not-found"
        assert result["errors"][2]["extensions"]["code"] == "backendai_generic_internal-error"
        assert "serviceName" not in result["errors"][2]["extensions"]

    def test_error_without_extensions(self) -> None:
        data: dict = {
            "data": None,
            "errors": [
                {
                    "message": "Some error",
                }
            ],
        }
        result = _transform_downstream_service_errors(data)
        assert result == data

    def test_error_with_non_dict_extensions(self) -> None:
        data: dict = {
            "data": None,
            "errors": [
                {
                    "message": "Some error",
                    "extensions": "invalid",
                }
            ],
        }
        result = _transform_downstream_service_errors(data)
        assert result == data
