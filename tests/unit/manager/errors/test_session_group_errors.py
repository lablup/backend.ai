from __future__ import annotations

from http import HTTPStatus

from ai.backend.manager.errors.session_group import SessionGroupInUse


class TestSessionGroupInUse:
    def test_reports_a_conflict(self) -> None:
        error = SessionGroupInUse("boom")

        assert error.status_code == HTTPStatus.CONFLICT

    def test_carries_a_problem_body(self) -> None:
        error = SessionGroupInUse("boom")

        assert error.body_dict["msg"] == "boom"
        assert error.content_type == "application/problem+json"
