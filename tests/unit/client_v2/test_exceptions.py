from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.exceptions import (
    AuthenticationError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    ServerError,
    TooManyRequestsError,
    map_status_to_exception,
)


class TestMapStatusToException:
    def test_400_returns_invalid_request(self) -> None:
        exc = map_status_to_exception(400, "Bad Request", {})
        assert isinstance(exc, InvalidRequestError)
        assert exc.status == 400

    def test_401_returns_authentication_error(self) -> None:
        exc = map_status_to_exception(401, "Unauthorized", {})
        assert isinstance(exc, AuthenticationError)
        assert exc.status == 401

    def test_403_returns_permission_denied(self) -> None:
        exc = map_status_to_exception(403, "Forbidden", {})
        assert isinstance(exc, PermissionDeniedError)
        assert exc.status == 403

    def test_404_returns_not_found(self) -> None:
        exc = map_status_to_exception(404, "Not Found", {})
        assert isinstance(exc, NotFoundError)
        assert exc.status == 404

    def test_409_returns_conflict(self) -> None:
        exc = map_status_to_exception(409, "Conflict", {})
        assert isinstance(exc, ConflictError)
        assert exc.status == 409

    def test_429_returns_too_many_requests(self) -> None:
        exc = map_status_to_exception(429, "Too Many Requests", {})
        assert isinstance(exc, TooManyRequestsError)
        assert exc.status == 429

    def test_500_returns_server_error(self) -> None:
        exc = map_status_to_exception(500, "Internal Server Error", {})
        assert isinstance(exc, ServerError)
        assert exc.status == 500

    def test_502_returns_server_error(self) -> None:
        exc = map_status_to_exception(502, "Bad Gateway", {})
        assert isinstance(exc, ServerError)

    def test_503_returns_server_error(self) -> None:
        exc = map_status_to_exception(503, "Service Unavailable", {})
        assert isinstance(exc, ServerError)

    def test_unknown_4xx_returns_base_error(self) -> None:
        exc = map_status_to_exception(418, "I'm a Teapot", {})
        assert type(exc) is BackendAPIError
        assert exc.status == 418

    def test_all_are_backend_api_error_subclass(self) -> None:
        for status in [400, 401, 403, 404, 409, 429, 500]:
            exc = map_status_to_exception(status, "test", {})
            assert isinstance(exc, BackendAPIError)

    def test_preserves_reason_and_data(self) -> None:
        data = {"type": "error", "title": "test error"}
        exc = map_status_to_exception(404, "Not Found", data)
        assert exc.reason == "Not Found"
        assert exc.data == data
