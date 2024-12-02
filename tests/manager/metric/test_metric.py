from ai.backend.manager.metric.metric import MetricRegistry


def test_metric_registry_instance():
    registry1 = MetricRegistry()
    registry2 = MetricRegistry()

    assert registry1.api is not None
    assert registry1.api is registry2.api
    assert registry1.event is not None
    assert registry1.event is registry2.event
