"""
Common calculation utilities for usage bucket metrics.

These functions provide Fair Share metric calculations used across
domain, project, and user usage bucket types.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.fair_share.types import ResourceSlotGQL

SECONDS_PER_DAY = Decimal("86400")


def calculate_average_daily_usage(
    resource_usage: ResourceSlotGQL,
    period_start: date,
    period_end: date,
) -> ResourceSlotGQL:
    """
    Calculate average daily resource usage during the bucket period.

    For each resource type, computes: resource_usage / bucket_duration_days

    Args:
        resource_usage: Total resource usage in resource-seconds
        period_start: Bucket period start date
        period_end: Bucket period end date

    Returns:
        Average daily usage per resource type. Units match the resource type
        (e.g., CPU cores, memory bytes).

    Note:
        Returns empty ResourceSlotGQL if bucket duration is zero.
    """
    bucket_duration_days = Decimal((period_end - period_start).days)

    if bucket_duration_days == 0:
        return ResourceSlotGQL(entries=[])

    # Convert ResourceSlotGQL to ResourceSlot for calculation
    usage_slot = ResourceSlot({
        entry.resource_type: entry.quantity for entry in resource_usage.entries
    })
    avg_daily = ResourceSlot()

    for resource_type, quantity in usage_slot.items():
        avg_daily[resource_type] = quantity / bucket_duration_days

    return ResourceSlotGQL.from_resource_slot(avg_daily)


def calculate_usage_capacity_ratio(
    resource_usage: ResourceSlotGQL,
    capacity_snapshot: ResourceSlotGQL,
) -> ResourceSlotGQL:
    """
    Calculate usage ratio against total available capacity.

    For each resource type, computes: resource_usage / capacity_snapshot

    Args:
        resource_usage: Total resource usage in resource-seconds
        capacity_snapshot: Total available capacity snapshot

    Returns:
        Usage ratio in seconds. A value of 86400 means full utilization
        for one day. Values can exceed this if usage exceeds capacity.

    Note:
        Excludes resource types where capacity is zero to avoid division by zero.
    """
    # Convert ResourceSlotGQL to ResourceSlot for calculation
    usage_slot = ResourceSlot({
        entry.resource_type: entry.quantity for entry in resource_usage.entries
    })
    capacity_slot = ResourceSlot({
        entry.resource_type: entry.quantity for entry in capacity_snapshot.entries
    })
    ratio_slot = ResourceSlot()

    for resource_type, usage_quantity in usage_slot.items():
        capacity_quantity = capacity_slot.get(resource_type, Decimal(0))

        if capacity_quantity == 0:
            # Skip resources with zero capacity
            continue

        ratio_slot[resource_type] = usage_quantity / capacity_quantity

    return ResourceSlotGQL.from_resource_slot(ratio_slot)


def calculate_average_capacity_per_second(
    capacity_snapshot: ResourceSlotGQL,
    period_start: date,
    period_end: date,
) -> ResourceSlotGQL:
    """
    Calculate average available capacity per second during the bucket period.

    For each resource type, computes: capacity_snapshot / bucket_duration_seconds

    Args:
        capacity_snapshot: Total available capacity snapshot
        period_start: Bucket period start date
        period_end: Bucket period end date

    Returns:
        Average instantaneous capacity per resource type in resource/second units
        (e.g., CPU cores, memory bytes).

    Note:
        Returns empty ResourceSlotGQL if bucket duration is zero.
    """
    bucket_duration_days = Decimal((period_end - period_start).days)
    bucket_duration_seconds = bucket_duration_days * SECONDS_PER_DAY

    if bucket_duration_seconds == 0:
        return ResourceSlotGQL(entries=[])

    # Convert ResourceSlotGQL to ResourceSlot for calculation
    capacity_slot = ResourceSlot({
        entry.resource_type: entry.quantity for entry in capacity_snapshot.entries
    })
    avg_capacity = ResourceSlot()

    for resource_type, quantity in capacity_slot.items():
        avg_capacity[resource_type] = quantity / bucket_duration_seconds

    return ResourceSlotGQL.from_resource_slot(avg_capacity)
