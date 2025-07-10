from __future__ import annotations

import random

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    ValkeyRateLimitClient,
)


async def test_valkey_rate_limit_logic_execution(
    test_valkey_rate_limit: ValkeyRateLimitClient,
) -> None:
    """Test rate limiting logic execution."""
    access_key = f"test-logic-{random.randint(1000, 9999)}"

    # Execute the rate limiting logic
    result = await test_valkey_rate_limit.execute_rate_limit_logic(
        access_key=access_key,
        window=60,
    )

    assert result == 1  # First request should return 1

    # Execute again
    result2 = await test_valkey_rate_limit.execute_rate_limit_logic(
        access_key=access_key,
        window=60,
    )

    assert result2 == 2  # Second request should return 2
