from __future__ import annotations

import uuid

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID


async def test_valkey_rate_limit_logic_execution(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    """Test rate limiting logic execution."""
    user_id = UserID(uuid.uuid4())

    # Execute the rate limiting logic
    result = await test_valkey_rate_limit.execute_rate_limit_logic(
        user_id=user_id,
        window=60,
    )

    assert result == 1  # First request should return 1

    # Execute again
    result2 = await test_valkey_rate_limit.execute_rate_limit_logic(
        user_id=user_id,
        window=60,
    )

    assert result2 == 2  # Second request should return 2

    assert await test_valkey_rate_limit.get_rolling_count(user_id) == 2
