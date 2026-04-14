"""
Test script: Operation client recovery while monitor client is healthy.

Verifies the core BA-5577/BA-5578 scenario:
  1. Both operation and monitor clients are healthy
  2. Operation client becomes broken (disconnected)
  3. Monitor client remains healthy (ping succeeds)
  4. acquire() detects operation failures and triggers reconnect
  5. Operation client recovers without manager restart

Usage:
  ./py scripts/test_valkey_operation_recovery.py
"""

from __future__ import annotations

import asyncio
import sys
from typing import cast

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    create_valkey_client,
)
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.types import ValkeyTarget


async def main() -> None:
    valkey_target = ValkeyTarget(addr="localhost:8111")
    client = cast(
        MonitoringValkeyClient,
        create_valkey_client(
            valkey_target,
            db_id=REDIS_STREAM_DB,
            human_readable_name="test.operation-recovery",
        ),
    )
    await client.connect()

    threshold = client._spec.consecutive_failure_threshold
    print(f"consecutive_failure_threshold = {threshold}")
    print()

    try:
        # Step 1: Verify both clients are healthy
        print("=== Step 1: Verify both clients are healthy ===")
        await client._monitor_client.ping()
        print("  monitor client ping: OK")
        async with client.acquire() as conn:
            result = await conn.ping()
            print(f"  operation client ping: {result}")
        print()

        # Step 2: Break only the operation client
        print("=== Step 2: Disconnect operation client only ===")
        await client._operation_client.disconnect()
        print("  operation client disconnected")
        print()

        # Step 3: Verify monitor is still healthy
        print("=== Step 3: Verify monitor client is still healthy ===")
        await client._monitor_client.ping()
        print("  monitor client ping: OK (monitor cannot detect operation failure)")
        print()

        # Step 4: acquire() fails and tracks failures
        print(f"=== Step 4: acquire() failure tracking (threshold={threshold}) ===")
        for i in range(threshold):
            try:
                async with client.acquire() as conn:
                    await conn.ping()
            except Exception as e:
                print(f"  attempt {i + 1}/{threshold}: FAILED ({type(e).__name__}: {e})")
            print(f"  _operation_failure_count = {client._operation_failure_count}")

        print()

        # Step 5: Verify operation client recovered
        print("=== Step 5: Verify operation client recovered after reconnect ===")
        async with client.acquire() as conn:
            result = await conn.ping()
            print(f"  operation client ping: {result}")

        # Step 6: Monitor still healthy
        await client._monitor_client.ping()
        print("  monitor client ping: OK")
        print()

        print("=== RESULT: PASS ===")

    except Exception as e:
        print(f"\n=== RESULT: FAIL ({type(e).__name__}: {e}) ===")
        sys.exit(1)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
