from dataclasses import dataclass
from typing import Any

from ai.backend.manager.services.metric.types import DeviceMetricResult, MetricResultValue


@dataclass
class MetricByTypeValue:
    latest: MetricResultValue
    values: list[MetricResultValue]


def transform_device_metrics(source_data: list[DeviceMetricResult]) -> dict[str, Any]:
    """
    Transform Prometheus-styled device metrics data into a legacy `live_stat` format.
    """

    # Initialize result structure
    result: dict[str, dict[str, Any]] = {"devices": {}, "node": {}}

    # Group metrics by device_metric_name and device_id
    # Store both latest value and full values array for rate calculations
    metrics_by_type: dict[str, dict[str, dict[str, MetricByTypeValue]]] = {}

    for item in source_data:
        metric_name = item.metric.device_metric_name
        device_id = item.metric.device_id
        if metric_name is None:
            continue
        if device_id is None:
            continue
        value_type = item.metric.value_type

        if metric_name not in metrics_by_type:
            metrics_by_type[metric_name] = {}

        if device_id not in metrics_by_type[metric_name]:
            metrics_by_type[metric_name][device_id] = {}

        # Store both latest value and full values array
        if item.values:
            metrics_by_type[metric_name][device_id][value_type] = MetricByTypeValue(
                latest=item.values[-1],
                values=item.values,
            )

    # Process each metric type
    for metric_name, devices in metrics_by_type.items():
        if metric_name == "cpu_util":
            # Initialize devices dict for cpu_util
            result["devices"]["cpu_util"] = {}

            # Node level aggregation
            total_capacity = 0.0
            total_current = 0.0

            # Process each CPU device
            for device_id, values in devices.items():
                capacity_data = values.get("capacity")
                current_data = values.get("current")

                # Get capacity (latest value)
                capacity = capacity_data.latest.value if capacity_data is not None else "0"

                # Calculate current from diff of last two values
                current = "0"
                if current_data is not None:
                    current_values = current_data.values
                    if len(current_values) >= 2:
                        # CPU values are already diff values, so take the difference
                        last_value = float(current_values[-1].value)
                        prev_value = float(current_values[-2].value)
                        current = str(last_value - prev_value)

                # Calculate percentage for device
                try:
                    pct = float(current) / float(capacity) * 100
                    pct_str = f"{pct:.2f}"
                except ArithmeticError:
                    pct_str = "0.00"

                # Add device entry
                result["devices"]["cpu_util"][device_id] = {
                    "capacity": capacity,
                    "current": current,
                    "pct": pct_str,
                    "unit_hint": "msec",
                }

                # Accumulate for node total
                total_capacity += float(capacity)
                total_current += float(current)

            # Calculate node level CPU util
            try:
                node_pct = total_current / total_capacity * 100
                node_pct_str = f"{node_pct:.2f}"
            except ArithmeticError:
                node_pct_str = "0.00"

            result["node"]["cpu_util"] = {
                "capacity": str(total_capacity),
                "current": str(total_current),
                "pct": node_pct_str,
                "unit_hint": "msec",
            }

        elif metric_name == "disk":
            # Initialize devices dict for disk
            result["devices"]["disk"] = {}

            # Node level aggregation
            total_capacity = 0.0
            total_current = 0.0

            # Process each disk device
            for device_id, values in devices.items():
                capacity_data = values.get("capacity")
                current_data = values.get("current")

                # Get latest values
                capacity = capacity_data.latest.value if capacity_data is not None else "0"
                current = current_data.latest.value if current_data is not None else "0"

                # Calculate percentage for device
                try:
                    pct = float(current) / float(capacity) * 100
                    pct_str = f"{pct:.2f}"
                except ArithmeticError:
                    pct_str = "0.00"

                # Add device entry
                result["devices"]["disk"][device_id] = {
                    "capacity": capacity,
                    "current": current,
                    "pct": pct_str,
                    "unit_hint": "bytes",
                }

                # Accumulate for node total
                total_capacity += float(capacity)
                total_current += float(current)

            # Calculate node level disk
            try:
                node_pct = total_current / total_capacity * 100
                node_pct_str = f"{node_pct:.2f}"
            except ArithmeticError:
                node_pct_str = "0.00"

            result["node"]["disk"] = {
                "capacity": str(int(total_capacity)),
                "current": str(int(total_current)),
                "pct": node_pct_str,
                "unit_hint": "bytes",
            }

        elif metric_name == "mem":
            # Initialize devices dict for mem
            result["devices"]["mem"] = {}

            # Process memory devices (expecting "root" device)
            for device_id, values in devices.items():
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

                # Add device entry
                result["devices"]["mem"][device_id] = {
                    "capacity": capacity,
                    "current": current,
                    "pct": pct_str,
                    "stats.max": current,  # Using current as max
                    "unit_hint": "bytes",
                }

                # For node level, use the same values (assuming single memory pool)
                if device_id == "root":
                    result["node"]["mem"] = {
                        "capacity": capacity,
                        "current": current,
                        "pct": pct_str,
                        "stats.max": current,
                        "unit_hint": "bytes",
                    }

        elif metric_name == "net_rx":
            # Initialize devices dict for net_rx
            result["devices"]["net_rx"] = {}

            # Process network rx devices
            for device_id, values in devices.items():
                current_data = values.get("current")

                # Calculate rate (bps) from cumulative bytes
                rate = "0.00"
                if current_data is not None:
                    current_values = current_data.values
                    if len(current_values) >= 2:
                        # Get last two measurements
                        last = current_values[-1]
                        prev = current_values[-2]
                        last_time, last_bytes = last.timestamp, last.value
                        prev_time, prev_bytes = prev.timestamp, prev.value

                        # Calculate bytes per second, then convert to bits per second
                        time_diff = float(last_time) - float(prev_time)
                        bytes_diff = float(last_bytes) - float(prev_bytes)

                        if time_diff > 0:
                            bytes_per_sec = bytes_diff / time_diff
                            bits_per_sec = bytes_per_sec * 8
                            rate = f"{bits_per_sec:.3f}"

                result["devices"]["net_rx"][device_id] = {
                    "capacity": "None",
                    "current": rate,
                    "pct": "0.00",
                    "unit_hint": "bps",
                }

                # For node level
                if device_id == "node":
                    result["node"]["net_rx"] = {
                        "capacity": "None",
                        "current": rate,
                        "pct": "0.00",
                        "unit_hint": "bps",
                    }

        elif metric_name == "net_tx":
            # Initialize devices dict for net_tx
            result["devices"]["net_tx"] = {}

            # Process network tx devices
            for device_id, values in devices.items():
                current_data = values.get("current")

                # Calculate rate (bps) from cumulative bytes
                rate = "0.00"
                if current_data is not None:
                    current_values = current_data.values
                    if len(current_values) >= 2:
                        # Get last two measurements
                        last = current_values[-1]
                        prev = current_values[-2]
                        last_time, last_bytes = last.timestamp, last.value
                        prev_time, prev_bytes = prev.timestamp, prev.value

                        # Calculate bytes per second, then convert to bits per second
                        time_diff = float(last_time) - float(prev_time)
                        bytes_diff = float(last_bytes) - float(prev_bytes)

                        if time_diff > 0:
                            bytes_per_sec = bytes_diff / time_diff
                            bits_per_sec = bytes_per_sec * 8
                            rate = f"{bits_per_sec:.3f}"

                result["devices"]["net_tx"][device_id] = {
                    "capacity": "None",
                    "current": rate,
                    "pct": "0.00",
                    "unit_hint": "bps",
                }

                # For node level
                if device_id == "node":
                    result["node"]["net_tx"] = {
                        "capacity": "None",
                        "current": rate,
                        "pct": "0.00",
                        "unit_hint": "bps",
                    }

        # Handle other metrics with _util or _mem suffix (use latest value only)
        elif metric_name.endswith("_util") or metric_name.endswith("_mem"):
            # Skip cpu_util and mem as they have specific logic above
            if metric_name in ["cpu_util", "mem"]:
                continue

            # Initialize devices dict for this metric
            result["devices"][metric_name] = {}

            # Process each device
            for device_id, values in devices.items():
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

                # Add device entry
                result["devices"][metric_name][device_id] = {
                    "capacity": capacity,
                    "current": current,
                    "pct": pct_str,
                    "unit_hint": "bytes" if metric_name.endswith("_mem") else "msec",
                }

    return result
