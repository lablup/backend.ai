from datetime import datetime, timezone
from decimal import Decimal

from ai.backend.common.types import (
    AgentId,
    BinarySize,
    ResourceSlot,
)
from ai.backend.manager.models.agent import AgentRow, AgentStatus
from ai.backend.manager.services.agent.types import AgentData

# Test agent IDs
TEST_AGENT_ID = AgentId("00000000-0000-0000-0000-000000000001")
TEST_AGENT_ID_2 = AgentId("00000000-0000-0000-0000-000000000002")
NONEXISTENT_AGENT_ID = AgentId("99999999-9999-9999-9999-999999999999")

# Test scaling group
TEST_SCALING_GROUP = "default"

# Test resource slots
TEST_AVAILABLE_SLOTS = ResourceSlot({
    "cpu": Decimal("24"),
    "mem": BinarySize.from_str("32G"),
    "cuda.shares": Decimal("4"),
})

TEST_OCCUPIED_SLOTS = ResourceSlot({
    "cpu": Decimal("8"),
    "mem": BinarySize.from_str("16G"),
    "cuda.shares": Decimal("2"),
})

# Test agent row fixture
AGENT_ROW_FIXTURE = AgentRow(
    id=TEST_AGENT_ID,
    scaling_group=TEST_SCALING_GROUP,
    status=AgentStatus.ALIVE,
    status_changed=datetime.now(timezone.utc),
    region="us-east-1",
    architecture="x86_64",
    addr="10.0.0.1:6001",
    public_host="agent1.example.com",
    public_key="test-public-key",
    available_slots=TEST_AVAILABLE_SLOTS,
    occupied_slots=TEST_OCCUPIED_SLOTS,
    version="24.03.0",
    compute_plugins=[],
    schedulable=True,
    lost_at=None,
    first_contact=datetime.now(timezone.utc),
)

# Test agent data fixture (DTO)
AGENT_DATA_FIXTURE = AgentData(
    id=TEST_AGENT_ID,
    scaling_group=TEST_SCALING_GROUP,
    status=AgentStatus.ALIVE,
    status_changed=datetime.now(timezone.utc),
    region="us-east-1",
    architecture="x86_64",
    addr="10.0.0.1:6001",
    public_host="agent1.example.com",
    available_slots=TEST_AVAILABLE_SLOTS,
    occupied_slots=TEST_OCCUPIED_SLOTS,
    version="24.03.0",
    compute_plugins=[],
    schedulable=True,
    first_contact=datetime.now(timezone.utc),
    lost_at=None,
)

# Watcher response fixtures
WATCHER_STATUS_RESPONSE = {
    "status": "running",
    "version": "24.03.0",
    "uptime": 3600,
    "plugins": ["docker", "jail"],
}

WATCHER_SUCCESS_RESPONSE = {
    "success": True,
    "message": "Operation completed successfully",
}

WATCHER_ERROR_RESPONSE = {
    "success": False,
    "error": "Connection refused",
}

# Modify agent input fixture
MODIFY_AGENT_INPUT_DICT = {
    "schedulable": False,
    "scaling_group": "new-group",
}
