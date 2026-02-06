from __future__ import annotations

from typing import Any, cast

import pytest

from ai.backend.common.metrics.metric import GraphQLMetricObserver


@pytest.fixture(scope="module")
def observer() -> GraphQLMetricObserver:
    cast(Any, GraphQLMetricObserver)._instance = None
    return GraphQLMetricObserver.instance()


class TestGraphQLMetricObserverPhase:
    def test_observe_phase_records_histogram(self, observer: GraphQLMetricObserver) -> None:
        """Phase metrics are recorded for GraphQL requests."""
        observer.observe_phase(
            operation="RecordTest",
            phase="gql_setup",
            duration=0.05,
        )
        sample_value = observer._phase_duration_sec.labels(
            operation="RecordTest",
            phase="gql_setup",
        )._sum.get()
        assert sample_value == pytest.approx(0.05)

    def test_observe_phase_all_three_phases(self, observer: GraphQLMetricObserver) -> None:
        """All three phases (gql_setup, gql_execute, serialize) are captured."""
        phases = {
            "gql_setup": 0.01,
            "gql_execute": 0.5,
            "serialize": 0.002,
        }
        for phase, duration in phases.items():
            observer.observe_phase(
                operation="ThreePhaseTest",
                phase=phase,
                duration=duration,
            )
        for phase, expected_duration in phases.items():
            sample_value = observer._phase_duration_sec.labels(
                operation="ThreePhaseTest",
                phase=phase,
            )._sum.get()
            assert sample_value == pytest.approx(expected_duration)

    def test_phase_durations_sum_approximately_to_total(
        self, observer: GraphQLMetricObserver
    ) -> None:
        """Phase durations sum approximately to total request duration."""
        setup_dur = 0.01
        execute_dur = 0.5
        serialize_dur = 0.002
        total_dur = 0.515

        observer.observe_phase(operation="SumTest", phase="gql_setup", duration=setup_dur)
        observer.observe_phase(operation="SumTest", phase="gql_execute", duration=execute_dur)
        observer.observe_phase(operation="SumTest", phase="serialize", duration=serialize_dur)

        phase_sum = setup_dur + execute_dur + serialize_dur
        assert phase_sum <= total_dur
        assert phase_sum >= total_dur * 0.9

    def test_operation_label_propagated(self, observer: GraphQLMetricObserver) -> None:
        """Operation label is correctly propagated to phase metrics."""
        observer.observe_phase(
            operation="FetchSessions",
            phase="gql_execute",
            duration=0.1,
        )
        observer.observe_phase(
            operation="CreateSession",
            phase="gql_execute",
            duration=0.2,
        )
        fetch_value = observer._phase_duration_sec.labels(
            operation="FetchSessions",
            phase="gql_execute",
        )._sum.get()
        create_value = observer._phase_duration_sec.labels(
            operation="CreateSession",
            phase="gql_execute",
        )._sum.get()
        assert fetch_value == pytest.approx(0.1)
        assert create_value == pytest.approx(0.2)

    def test_anonymous_operation_name(self, observer: GraphQLMetricObserver) -> None:
        """Anonymous operations (no operation name) are recorded correctly."""
        observer.observe_phase(
            operation="anonymous",
            phase="gql_setup",
            duration=0.01,
        )
        sample_value = observer._phase_duration_sec.labels(
            operation="anonymous",
            phase="gql_setup",
        )._sum.get()
        assert sample_value == pytest.approx(0.01)

    def test_histogram_buckets(self, observer: GraphQLMetricObserver) -> None:
        """The histogram uses the correct custom bucket boundaries."""
        expected_buckets = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float("inf")]
        labeled = observer._phase_duration_sec.labels(operation="BucketTest", phase="test")
        assert list(labeled._upper_bounds) == expected_buckets
