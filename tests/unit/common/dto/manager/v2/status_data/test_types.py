"""Tests for ai.backend.common.dto.manager.v2.status_data.types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.status_data import (
    ErrorDetailInfo,
    KernelStatusBranch,
    KernelStatusData,
    SchedulerStatusBranch,
    SchedulingPredicateInfo,
    SessionStatusBranch,
)


class TestKernelStatusBranch:
    def test_parse_exit_code(self) -> None:
        branch = KernelStatusBranch.model_validate({"exit_code": 0})
        assert branch.exit_code == 0

    def test_default_exit_code_is_none(self) -> None:
        assert KernelStatusBranch().exit_code is None


class TestSessionStatusBranch:
    def test_parse_status(self) -> None:
        branch = SessionStatusBranch.model_validate({"status": "RUNNING"})
        assert branch.status == "RUNNING"


class TestSchedulerStatusBranch:
    def test_full_payload_round_trip(self) -> None:
        payload = {
            "msg": "no available agent",
            "retries": 3,
            "last_try": "2026-04-27T12:00:00Z",
            "passed_predicates": [{"name": "reserved_time"}],
            "failed_predicates": [{"name": "concurrency", "msg": "limit exceeded"}],
        }
        branch = SchedulerStatusBranch.model_validate(payload)
        assert branch.retries == 3
        assert branch.passed_predicates[0] == SchedulingPredicateInfo(name="reserved_time")
        assert branch.failed_predicates[0].msg == "limit exceeded"

    def test_empty_predicates_default_to_lists(self) -> None:
        branch = SchedulerStatusBranch()
        assert branch.passed_predicates == []
        assert branch.failed_predicates == []


class TestKernelStatusDataLegacyErrorParsing:
    """The model must tolerantly parse both legacy error shapes (#679)."""

    def test_legacy_single_error_is_normalized_to_list(self) -> None:
        legacy = {
            "error": {
                "src": "agent",
                "name": "ContainerCreationError",
                "repr": "ContainerCreationError('oom')",
                "agent_id": "agent-001",
            }
        }
        data = KernelStatusData.model_validate(legacy)
        assert data.errors == [
            ErrorDetailInfo(
                src="agent",
                name="ContainerCreationError",
                repr="ContainerCreationError('oom')",
                agent_id="agent-001",
            )
        ]

    def test_legacy_multi_agent_error_collection_is_flattened(self) -> None:
        legacy = {
            "error": {
                "src": "agent",
                "name": "MultiAgentError",
                "repr": "MultiAgentError(2)",
                "collection": [
                    {"src": "agent", "name": "E1", "repr": "E1()", "agent_id": "a1"},
                    {"src": "agent", "name": "E2", "repr": "E2()", "agent_id": "a2"},
                ],
            }
        }
        data = KernelStatusData.model_validate(legacy)
        assert [e.name for e in data.errors] == ["E1", "E2"]
        assert [e.agent_id for e in data.errors] == ["a1", "a2"]

    def test_new_errors_field_is_preserved_as_is(self) -> None:
        new_shape = {
            "errors": [
                {"src": "agent", "name": "X", "repr": "X()"},
            ]
        }
        data = KernelStatusData.model_validate(new_shape)
        assert len(data.errors) == 1
        assert data.errors[0].name == "X"

    def test_new_errors_takes_precedence_over_legacy_error(self) -> None:
        mixed = {
            "errors": [{"src": "other", "name": "New", "repr": "New()"}],
            "error": {"src": "agent", "name": "Old", "repr": "Old()"},
        }
        data = KernelStatusData.model_validate(mixed)
        assert [e.name for e in data.errors] == ["New"]

    def test_no_error_branch_yields_empty_list(self) -> None:
        data = KernelStatusData.model_validate({})
        assert data.errors == []


class TestKernelStatusDataAllBranches:
    def test_full_envelope_parses_all_branches(self) -> None:
        payload = {
            "kernel": {"exit_code": 137},
            "session": {"status": "TERMINATED"},
            "scheduler": {
                "msg": "ok",
                "retries": 1,
                "last_try": "2026-04-27T12:00:00Z",
                "passed_predicates": [],
                "failed_predicates": [],
            },
            "error": {"src": "agent", "name": "OOM", "repr": "OOM()"},
        }
        data = KernelStatusData.model_validate(payload)
        assert data.kernel == KernelStatusBranch(exit_code=137)
        assert data.session == SessionStatusBranch(status="TERMINATED")
        assert data.scheduler is not None
        assert data.scheduler.retries == 1
        assert len(data.errors) == 1
        assert data.errors[0].name == "OOM"

    def test_serialization_emits_canonical_errors_only(self) -> None:
        data = KernelStatusData(errors=[ErrorDetailInfo(src="agent", name="X", repr="X()")])
        dumped = data.model_dump(exclude_none=True)
        assert "error" not in dumped
        assert dumped["errors"] == [{"src": "agent", "name": "X", "repr": "X()"}]

    def test_unknown_top_level_keys_are_ignored(self) -> None:
        # DB rows may carry extra keys we have not modeled yet; do not crash.
        payload = {"kernel": {"exit_code": 0}, "future_field": {"x": 1}}
        data = KernelStatusData.model_validate(payload)
        assert data.kernel is not None
        assert data.kernel.exit_code == 0
