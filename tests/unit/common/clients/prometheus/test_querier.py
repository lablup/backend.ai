from uuid import UUID

from ai.backend.common.clients.prometheus import ContainerMetricQuerier, ValueType


class TestContainerMetricQuerierLabels:
    """Tests for ContainerMetricQuerier.labels() method."""

    async def test_labels_with_required_fields_only_returns_metric_name_and_value_type(
        self,
    ) -> None:
        """Test that labels() returns only required fields when optionals are None."""
        querier = ContainerMetricQuerier(
            metric_name="cpu_util",
            value_type=ValueType.CURRENT,
        )

        result = querier.labels()

        assert result == {
            "container_metric_name": "cpu_util",
            "value_type": "current",
        }

    async def test_labels_with_all_fields_includes_all(self) -> None:
        """Test that labels() includes all fields when set."""
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

    async def test_group_by_labels_with_kernel_id_includes_kernel_id(self) -> None:
        """Test that group_by_labels() includes kernel_id when set."""
        kernel_id = UUID("12345678-1234-5678-1234-567812345678")
        querier = ContainerMetricQuerier(
            metric_name="mem",
            value_type=ValueType.CURRENT,
            kernel_id=kernel_id,
        )

        result = querier.group_by_labels()

        assert "value_type" in result
        assert "kernel_id" in result

    async def test_group_by_labels_with_all_fields_includes_all(self) -> None:
        """Test that group_by_labels() includes all set fields."""
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

        assert "value_type" in result
        assert "kernel_id" in result
        assert "session_id" in result
        assert "agent_id" in result
        assert "user_id" in result
        assert "project_id" in result
