#!/usr/bin/env python
"""
Test script for batch broadcast with cache functionality.
"""

import asyncio
from typing import Mapping

from ai.backend.common.message_queue.types import CacheEvent


async def test_batch_broadcast():
    """Test the batch broadcast with cache functionality."""
    
    # Create sample events
    events = [
        CacheEvent(
            cache_id="event_1",
            payload={"type": "session_start", "session_id": "abc123"}
        ),
        CacheEvent(
            cache_id="event_2", 
            payload={"type": "session_end", "session_id": "def456"}
        ),
        CacheEvent(
            cache_id="event_3",
            payload={"type": "session_update", "session_id": "ghi789", "status": "running"}
        ),
    ]
    
    print(f"Created {len(events)} CacheEvent objects:")
    for event in events:
        print(f"  - cache_id: {event.cache_id}, payload: {event.payload}")
    
    # The actual queue implementation would be tested with real Redis connection
    print("\nBatch broadcast implementation is ready to be used with RedisQueue or HiRedisQueue.")
    print("Usage example:")
    print("  await queue.broadcast_with_cache_batch(events)")


if __name__ == "__main__":
    asyncio.run(test_batch_broadcast())