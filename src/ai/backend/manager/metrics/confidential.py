from typing import Self

from ai.backend.common.metrics.safe import SafeCounter as Counter
from ai.backend.common.metrics.safe import SafeGauge as Gauge
from ai.backend.manager.models.confidential.types import DecisionActor, DecisionVerdict


class ConfidentialMetricObserver:
    _instance: Self | None = None

    _decision_count: Counter
    _policy_upload_count: Counter
    _orphan_swept_count: Counter
    _tcb_grace_active: Gauge

    def __init__(self) -> None:
        self._decision_count = Counter(
            name="backendai_confidential_decision_count",
            documentation="Broker release decisions recorded by the authorisation shim",
            labelnames=["actor", "verdict"],
        )
        self._policy_upload_count = Counter(
            name="backendai_confidential_policy_upload_count",
            documentation="Release-policy documents composed and uploaded per broker endpoint",
            labelnames=["status"],
        )
        self._orphan_swept_count = Counter(
            name="backendai_confidential_orphan_swept_count",
            documentation="Session-scoped broker resources deleted by the orphan reconciler",
            labelnames=[],
        )
        self._tcb_grace_active = Gauge(
            name="backendai_confidential_tcb_grace_active",
            documentation="Broker endpoints running under a trusted-computing-base grace window",
            labelnames=["endpoint"],
        )

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_decision(self, actor: DecisionActor, verdict: DecisionVerdict) -> None:
        self._decision_count.labels(actor=actor.value, verdict=verdict.value).inc()

    def observe_policy_upload(self, status: str) -> None:
        self._policy_upload_count.labels(status=status).inc()

    def observe_orphans_swept(self, count: int) -> None:
        if count:
            self._orphan_swept_count.inc(count)

    def observe_tcb_grace(self, endpoint: str, active: bool) -> None:
        self._tcb_grace_active.labels(endpoint=endpoint).set(1 if active else 0)
