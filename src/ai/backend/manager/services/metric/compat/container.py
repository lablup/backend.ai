from dataclasses import dataclass
from typing import Any

from ai.backend.common.clients.prometheus.types import ContainerUtilizationQueryResult, ResultValue


@dataclass
class MetricByTypeValue:
    latest: ResultValue
    values: list[ResultValue]


def transform_container_metrics(
    source_data: list[ContainerUtilizationQueryResult],
) -> dict[str, Any]:
    """
    Transform Prometheus-styled container metrics data into a legacy `live_stat` format.
    """

    # Initialize result structure
    result: dict[str, Any] = {}

    # Group metrics by container_metric_name and value_type
    metrics_by_name: dict[str, dict[str, MetricByTypeValue]] = {}

    for item in source_data:
        metric_name = item.metric.container_metric_name
        value_type = item.metric.value_type
        if metric_name is None:
            continue

        if metric_name not in metrics_by_name:
            metrics_by_name[metric_name] = {}

        # Store both latest value and full values array
        if item.values:
            metrics_by_name[metric_name][value_type] = MetricByTypeValue(
                latest=item.values[-1],
                values=item.values,
            )

    # Process each metric type
    for metric_name, values in metrics_by_name.items():
        if metric_name == "cpu_used":
            current_data = values.get("current")

            # Get latest value
            current = current_data.latest.value if current_data is not None else "0"

            # Calculate capacity from values (use average as capacity)
            capacity = current
            if current_data is not None:
                all_values = [float(v.value) for v in current_data.values]
                if all_values:
                    # Use average as capacity
                    capacity = f"{sum(all_values) / len(all_values):.3f}"

            # Calculate percentage
            try:
                pct = float(current) / float(capacity) * 100
                pct_str = f"{pct:.2f}"
            except ArithmeticError:
                pct_str = "0.00"

            result["cpu_used"] = {
                "capacity": capacity,
                "current": current,
                "pct": pct_str,
                "unit_hint": "msec",
            }

        elif metric_name == "cpu_util":
            capacity_data = values.get("capacity")
            current_data = values.get("current")

            # Get capacity and current values
            capacity = capacity_data.latest.value if capacity_data is not None else "1000"

            # Calculate current from values if available
            current = "0"

            if current_data is not None:
                current_values = current_data.values
                if len(current_values) >= 2:
                    # CPU util values are already diff values
                    last_value = float(current_values[-1].value)
                    prev_value = float(current_values[-2].value)
                    current_diff = last_value - prev_value

                    # Calculate percentage based on capacity
                    current_pct = (
                        (current_diff / float(capacity)) * 100 if float(capacity) > 0 else 0
                    )
                    current = f"{current_pct:.3f}"

            # Calculate percentage (current / capacity * 100)
            try:
                pct = float(current) / float(capacity) * 100
                pct_str = f"{pct:.2f}"
            except ArithmeticError:
                pct_str = "0.00"

            result["cpu_util"] = {
                "capacity": capacity,
                "current": current,
                "pct": pct_str,
                "unit_hint": "percent",
            }

        elif metric_name == "mem":
            capacity_data = values.get("capacity")
            current_data = values.get("current")

            # Get latest values
            capacity = capacity_data.latest.value if capacity_data is not None else "0"
            current = current_data.latest.value if current_data is not None else "0"

            # Calculate percentage
            try:
                pct = float(current) / float(capacity) * 100
                pct_str = f"{pct:.2f}"
            except ArithmeticError:
                pct_str = "0.00"

            result["mem"] = {
                "capacity": capacity,
                "current": current,
                "pct": pct_str,
                "unit_hint": "bytes",
            }

        elif metric_name in ["net_rx", "net_tx"]:
            current_data = values.get("current")

            # Calculate rate (bps) from cumulative bytes
            rate = "0.000"

            if current_data is not None:
                current_values = current_data.values
                if len(current_values) >= 2:
                    # Get last two measurements
                    last_time, last_bytes = current_values[-1].timestamp, current_values[-1].value
                    prev_time, prev_bytes = current_values[-2].timestamp, current_values[-2].value

                    # Calculate bytes per second, then convert to bits per second
                    time_diff = float(last_time) - float(prev_time)
                    bytes_diff = float(last_bytes) - float(prev_bytes)

                    if time_diff > 0:
                        bytes_per_sec = bytes_diff / time_diff
                        bits_per_sec = bytes_per_sec * 8
                        rate = f"{bits_per_sec:.3f}"

            # For network metrics, set a reasonable capacity
            # Use a multiple of current rate as capacity
            try:
                rate_float = float(rate)
                # Set capacity as ~200x the current rate (to get percentage < 1%)
                capacity = f"{rate_float * 200:.0f}"
                pct = rate_float / float(capacity) * 100
                pct_str = f"{pct:.2f}"
            except ArithmeticError:
                capacity = rate
                pct_str = "0.00"

            result[metric_name] = {
                "capacity": capacity,
                "current": rate,
                "pct": pct_str,
                "unit_hint": "bps",
            }

        elif metric_name in ["io_read", "io_write"]:
            current_data = values.get("current")

            # Get latest value
            current = current_data.latest.value if current_data is not None else "0"

            result[metric_name] = {
                "capacity": "0",
                "current": current,
                "pct": "0.00",
                "unit_hint": "bytes",
            }

        elif metric_name == "io_scratch_size":
            current_data = values.get("current")

            # Get latest value
            current = current_data.latest.value if current_data is not None else "0"

            # Calculate max from all values
            if current_data is not None:
                all_values = [float(v.value) for v in current_data.values]

            result["io_scratch_size"] = {
                "capacity": "0",
                "current": current,
                "pct": "0.00",
                "unit_hint": "bytes",
            }

        elif metric_name == "cuda_mem":
            capacity_data = values.get("capacity")
            current_data = values.get("current")

            # Get latest values
            capacity = capacity_data.latest.value if capacity_data is not None else "0"
            current = current_data.latest.value if current_data is not None else "0"

            # Calculate percentage
            try:
                pct = float(current) / float(capacity) * 100
                pct_str = f"{pct:.2f}"
            except ArithmeticError:
                pct_str = "0.00"

            result["cuda_mem"] = {
                "capacity": capacity,
                "current": current,
                "pct": pct_str,
                "unit_hint": "bytes",
            }

        elif metric_name == "cuda_util":
            capacity_data = values.get("capacity")
            current_data = values.get("current")

            # Get capacity and latest current
            capacity = capacity_data.latest.value if capacity_data is not None else "100"
            current = current_data.latest.value if current_data is not None else "0"

            # Calculate percentage
            try:
                pct = float(current)  # cuda_util is already a percentage
                pct_str = f"{pct:.2f}"
            except ArithmeticError:
                pct_str = "0.00"

            result["cuda_util"] = {
                "capacity": capacity,
                "current": current,
                "pct": pct_str,
                "unit_hint": "percent",
            }

        # Handle other metrics with _util or _mem suffix (use latest value only)
        elif metric_name.endswith("_util") or metric_name.endswith("_mem"):
            # Skip already processed metrics
            if metric_name in ["cpu_util", "mem", "cuda_util", "cuda_mem"]:
                continue

            capacity_data = values.get("capacity")
            current_data = values.get("current")

            # Get latest values
            capacity = capacity_data.latest.value if capacity_data is not None else "0"
            current = current_data.latest.value if current_data is not None else "0"

            # Calculate percentage
            try:
                pct = float(current) / float(capacity) * 100 if float(capacity) > 0 else 0
                pct_str = f"{pct:.2f}"
            except ArithmeticError:
                pct_str = "0.00"

            # Add basic metrics
            result[metric_name] = {
                "capacity": capacity,
                "current": current,
                "pct": pct_str,
                "unit_hint": "bytes" if metric_name.endswith("_mem") else "percent",
            }

    return result
