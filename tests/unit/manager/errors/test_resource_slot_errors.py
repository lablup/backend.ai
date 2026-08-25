"""Resource slot errors must carry an HTTP status.

``BackendAIError`` derives from ``web.HTTPError`` but fixes no status of its
own, so an error that names no ``web.HTTP*`` base serialises as ``HTTP/1.1 -1``
— a status line no client can parse. It surfaces as a transport failure rather
than the domain error, and only over a real server: the specs these errors are
raised from convert nothing, so unit tests at that layer stay green.
"""

from __future__ import annotations

from http import HTTPStatus

import pytest

from ai.backend.manager.errors.resource_slot import (
    AgentResourceCapacityExceeded,
    AgentResourceNotFound,
    ResourceAllocationNotFound,
    ResourceSlotTypeAlreadyExists,
    ResourceSlotTypeInUse,
    ResourceSlotTypeNotFound,
)

_EXPECTED_STATUSES = [
    (ResourceSlotTypeNotFound, HTTPStatus.NOT_FOUND),
    (AgentResourceNotFound, HTTPStatus.NOT_FOUND),
    (ResourceAllocationNotFound, HTTPStatus.NOT_FOUND),
    (ResourceSlotTypeAlreadyExists, HTTPStatus.CONFLICT),
    (ResourceSlotTypeInUse, HTTPStatus.CONFLICT),
    (AgentResourceCapacityExceeded, HTTPStatus.CONFLICT),
]


class TestResourceSlotErrorStatuses:
    @pytest.mark.parametrize(
        ("error_cls", "expected"),
        _EXPECTED_STATUSES,
        ids=[cls.__name__ for cls, _ in _EXPECTED_STATUSES],
    )
    def test_error_reports_its_http_status(
        self, error_cls: type[Exception], expected: HTTPStatus
    ) -> None:
        error = error_cls("boom")
        assert error.status_code == expected  # type: ignore[attr-defined]

    @pytest.mark.parametrize(
        ("error_cls", "expected"),
        _EXPECTED_STATUSES,
        ids=[cls.__name__ for cls, _ in _EXPECTED_STATUSES],
    )
    def test_error_carries_a_problem_body(
        self, error_cls: type[Exception], expected: HTTPStatus
    ) -> None:
        error = error_cls("boom")
        assert error.body_dict["msg"] == "boom"  # type: ignore[attr-defined]
        assert error.content_type == "application/problem+json"  # type: ignore[attr-defined]
