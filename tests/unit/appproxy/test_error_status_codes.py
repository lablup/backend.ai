"""
Verify that AppProxy error classes return correct HTTP status codes.

BackendAIError inherits from aiohttp.web.HTTPException which defaults
to status_code = -1. Each error class must also inherit from a concrete
HTTP exception (e.g. web.HTTPNotFound) to get a valid status code.
"""

import inspect
from types import ModuleType

import pytest

from ai.backend.appproxy.common.errors import (
    AuthorizationFailed,
    GenericBadRequest,
    GenericForbidden,
    InsufficientPrivilege,
    InternalServerError,
    InvalidAPIParameters,
    InvalidAuthParameters,
    InvalidCredentials,
    MethodNotAllowed,
    ObjectNotFound,
    PasswordExpired,
    QueryNotImplemented,
    ServerMisconfiguredError,
    ServiceUnavailable,
    URLNotFound,
)
from ai.backend.appproxy.common.errors import config as common_config_errors
from ai.backend.appproxy.common.errors import http as common_http_errors
from ai.backend.appproxy.common.errors import service as common_service_errors
from ai.backend.appproxy.coordinator.errors import circuit as coordinator_circuit_errors
from ai.backend.appproxy.coordinator.errors import config as coordinator_config_errors
from ai.backend.appproxy.coordinator.errors import ingress as coordinator_ingress_errors
from ai.backend.appproxy.worker.errors import circuit as worker_circuit_errors
from ai.backend.appproxy.worker.errors import config as worker_config_errors
from ai.backend.appproxy.worker.errors import ingress as worker_ingress_errors
from ai.backend.appproxy.worker.errors import process as worker_process_errors
from ai.backend.common.exception import BackendAIError


@pytest.mark.parametrize(
    "error_cls, expected_status",
    [
        (URLNotFound, 404),
        (ObjectNotFound, 404),
        (GenericBadRequest, 400),
        (InvalidCredentials, 401),
        (AuthorizationFailed, 401),
        (PasswordExpired, 401),
        (GenericForbidden, 403),
        (InsufficientPrivilege, 403),
        (InvalidAuthParameters, 400),
        (InvalidAPIParameters, 400),
        (InternalServerError, 500),
        (ServerMisconfiguredError, 500),
        (ServiceUnavailable, 503),
        (QueryNotImplemented, 501),
    ],
)
def test_error_status_codes(error_cls: type[BackendAIError], expected_status: int) -> None:
    assert error_cls.status_code == expected_status, (
        f"{error_cls.__name__} has status_code={error_cls.status_code}, expected {expected_status}"
    )


@pytest.fixture
def error_classes_in_appproxy_error_modules() -> list[type[BackendAIError]]:
    error_modules: list[ModuleType] = [
        common_config_errors,
        common_http_errors,
        common_service_errors,
        coordinator_circuit_errors,
        coordinator_config_errors,
        coordinator_ingress_errors,
        worker_circuit_errors,
        worker_config_errors,
        worker_ingress_errors,
        worker_process_errors,
    ]
    return [
        cls
        for module in error_modules
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BackendAIError) and cls.__module__ == module.__name__
    ]


def test_no_error_class_keeps_the_default_status_code(
    error_classes_in_appproxy_error_modules: list[type[BackendAIError]],
) -> None:
    classes_without_status = [
        f"{cls.__module__}.{cls.__qualname__}"
        for cls in error_classes_in_appproxy_error_modules
        if cls.status_code == -1
    ]
    assert classes_without_status == []


def test_method_not_allowed_with_extra_msg() -> None:
    err = MethodNotAllowed(
        extra_msg="Method GET not allowed",
        extra_data={"allowed_methods": ["POST"]},
    )
    assert err.status_code == 405
