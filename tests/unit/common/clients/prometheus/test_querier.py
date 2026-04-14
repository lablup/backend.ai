from uuid import UUID

from ai.backend.common.clients.prometheus import ContainerMetricQuerier, ValueType


class TestContainerMetricQuerier:
    """Tests for ContainerMetricQuerier."""

    async def test_labels_required_only(self) -> None:
        querier = ContainerMetricQuerier(
            metric_name="cpu_util",
            value_type=ValueType.CURRENT,
        )

        result = querier.labels()

        assert result == {
            "container_metric_name": "cpu_util",
            "value_type": "current",
        }

    async def test_labels_all_fields(self) -> None:
        kernel_id = UUID("12345678-1234-5678-1234-567812345678")
        session_id = UUID("22345678-1234-5678-1234-567812345678")
        user_id = UUID("32345678-1234-5678-1234-567812345678")
        project_id = UUID("42345678-1234-5678-1234-567812345678")

        querier = ContainerMetricQuerier(
            metric_name="net_rx",
            value_type=ValueType.CURRENT,
            kernel_id=kernel_id,
            session_id=session_id,
            agent_id="agent-001",
            user_id=user_id,
            project_id=project_id,
        )

        result = querier.labels()

        assert result == {
            "container_metric_name": "net_rx",
            "value_type": "current",
            "kernel_id": str(kernel_id),
            "session_id": str(session_id),
            "agent_id": "agent-001",
            "user_id": str(user_id),
            "project_id": str(project_id),
        }

    async def test_group_by_required_only(self) -> None:
        querier = ContainerMetricQuerier(
            metric_name="cpu_util",
            value_type=ValueType.CURRENT,
        )

        result = querier.group_by_labels()

        assert result == frozenset({"value_type"})

    async def test_group_by_with_kernel_id(self) -> None:
        querier = ContainerMetricQuerier(
            metric_name="mem",
            value_type=ValueType.CURRENT,
            kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
        )

        result = querier.group_by_labels()

        assert result == frozenset({"value_type", "kernel_id"})

    async def test_group_by_all_fields(self) -> None:
        querier = ContainerMetricQuerier(
            metric_name="net_rx",
            value_type=ValueType.CURRENT,
            kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
            session_id=UUID("22345678-1234-5678-1234-567812345678"),
            agent_id="agent-001",
            user_id=UUID("32345678-1234-5678-1234-567812345678"),
            project_id=UUID("42345678-1234-5678-1234-567812345678"),
        )

        result = querier.group_by_labels()

        assert result == frozenset({
            "value_type",
            "kernel_id",
            "session_id",
            "agent_id",
            "user_id",
            "project_id",
        })
