from __future__ import annotations

import logging
from typing import Any

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def clamp_agent_cpu_util(stat_data: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Clamp agent CPU utilization to the maximum of cpu_count * 100.

    This prevents reported CPU utilization from exceeding the theoretical
    maximum based on the number of CPU cores. When clamping occurs, a debug
    log is emitted.

    :param stat_data: Agent statistics data containing node and device metrics
    :return: The same stat_data with clamped CPU utilization values
    """
    if not stat_data:
        return stat_data

    # Early return if no CPU info
    devices_cpu = stat_data.get("devices", {}).get("cpu_util", {})
    num_cores = len(devices_cpu)
    if num_cores == 0:
        return stat_data

    max_cpu_util = num_cores * 100

    # Early return if no node cpu_util
    node_cpu_util = stat_data.get("node", {}).get("cpu_util")
    if not node_cpu_util:
        return stat_data

    # Clamp all relevant fields and track changes
    clamped_fields = False
    original_cpu_util = 0
    for field in ("current", "pct"):
        if field in node_cpu_util:
            original = node_cpu_util[field]
            if original > max_cpu_util:
                node_cpu_util[field] = max_cpu_util
                clamped_fields = True
                original_cpu_util = original  # Record the original value only when clamping

    if clamped_fields:
        log.debug(
            "Clamped CPU utilization from {} to {} (max: {} cores * 100)",
            original_cpu_util,
            max_cpu_util,
            num_cores,
        )

    return stat_data
