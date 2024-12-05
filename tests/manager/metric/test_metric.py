from ai.backend.manager.metric.metric import MetricRegistry


def test_metric_registry_instance():
    registry1 = MetricRegistry()
    registry2 = MetricRegistry()

    assert registry1.common is not None
    assert registry1.common is registry2.common
