from typing import Final

UNDEFINED: Final[str] = "undefined"

# Label values for the boolean "success" metric label (matching ``str(bool)``).
SUCCESS_LABEL_TRUE: Final[str] = "True"
SUCCESS_LABEL_FALSE: Final[str] = "False"

UTILIZATION_METRIC_DETENTION: Final[float] = 600.0  # 10 minutes

CONTAINER_UTILIZATION_METRIC_NAME: Final[str] = "backendai_container_utilization"
CONTAINER_UTILIZATION_METRIC_LABEL_NAME: Final[str] = "container_metric_name"
DEVICE_UTILIZATION_METRIC_LABEL_NAME: Final[str] = "device_metric_name"
PROCESS_UTILIZATION_METRIC_LABEL_NAME: Final[str] = "process_metric_name"

# Stand-in capacity for metrics whose Prometheus capacity series does not exist.
CAPACITY_SENTINEL: Final[str] = "9223372036854775807"  # 2**63 - 1

CAPACITY_SENTINEL_METRICS: Final[frozenset[str]] = frozenset({
    "cpu_used",
    "net_rx",
    "net_tx",
    "io_read",
    "io_write",
})
