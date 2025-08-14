from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ScheduleDBSource:
    """
    ScheduleDBSource is a class that provides methods to interact with the schedule database.
    It is used to manage and retrieve schedule-related data.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db_source):
        self.db_source = db_source

    async def get_schedule(self, schedule_id):
        """
        Retrieves a schedule by its ID.

        :param schedule_id: The ID of the schedule to retrieve.
        :return: The schedule object if found, None otherwise.
        """
        return await self.db_source.get(schedule_id)
