"""Test utilities for sokovan scheduler tests."""

from uuid import uuid4

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload


def create_session_workload(**kwargs):
    """Create a SessionWorkload with default values for testing."""
    defaults = {
        "session_id": SessionId(uuid4()),
        "access_key": AccessKey("test-key"),
        "requested_slots": ResourceSlot({"cpu": 1, "memory": 1}),
        "user_uuid": uuid4(),
        "group_id": uuid4(),
        "domain_name": "default",
        "scaling_group": "default",
        "priority": 0,
        "session_type": SessionTypes.INTERACTIVE,
        "cluster_mode": ClusterMode.SINGLE_NODE,
        "starts_at": None,
        "is_private": False,
        "kernels": [],
        "designated_agent": None,
        "kernel_counts_at_endpoint": None,
    }

    # Override with provided kwargs
    defaults.update(kwargs)

    return SessionWorkload(**defaults)
