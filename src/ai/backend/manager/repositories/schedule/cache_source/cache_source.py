class ScheduleCacheSource:
    """
    ScheduleCacheSource is a class that provides an interface for managing
    schedule-related data in a cache, specifically using Redis.
    """

    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def get_schedule(self, schedule_id: str):
        """
        Retrieve a schedule by its ID from the cache.
        """
        return await self.redis_client.get(schedule_id)

    async def set_schedule(self, schedule_id: str, schedule_data: dict):
        """
        Store a schedule in the cache with its ID.
        """
        await self.redis_client.set(schedule_id, schedule_data)
