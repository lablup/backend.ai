from ai.backend.manager.services.groups.processors import GroupProcessors


class Processors:
    group: GroupProcessors

    def __init__(self, group_processor: GroupProcessors) -> None:
        self.group = group_processor
