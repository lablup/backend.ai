from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
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

    # Early return if no node cpu_util
    node_cpu_util = stat_data.get("node", {}).get("cpu_util")
    if not node_cpu_util:
        return stat_data

    # Clamp pct
    original_pct = node_cpu_util.get("pct")
    if original_pct is not None:
        try:
            max_cpu_util = num_cores * 100
            if Decimal(original_pct) > Decimal(max_cpu_util):
                stat_data["node"]["cpu_util"]["pct"] = str(max_cpu_util)
                log.debug(
                    "Clamped node CPU utilization pct from {} to {} (max: {} cores * 100)",
                    original_pct,
                    max_cpu_util,
                    num_cores,
                )
        except InvalidOperation:
            log.warning("Invalid CPU utilization pct value: {}", original_pct)

    # Clamp current
    original_current = node_cpu_util.get("current")
    original_capacity = node_cpu_util.get("capacity")
    if original_current is not None and original_capacity is not None:
        try:
            max_current = Decimal(original_capacity) * num_cores
            if Decimal(original_current) > max_current:
                stat_data["node"]["cpu_util"]["current"] = str(max_current)
                log.debug(
                    "Clamped node CPU utilization current from {} to {} (capacity {} * {} cores)",
                    original_current,
                    max_current,
                    original_capacity,
                    num_cores,
                )
        except InvalidOperation:
            log.warning(
                "Invalid CPU utilization current/capacity value: current={}, capacity={}",
                original_current,
                original_capacity,
            )

    return stat_data
