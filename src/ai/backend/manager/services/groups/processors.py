from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.groups.actions.create_group import (
    CreateGroupAction,
    CreateGroupActionResult,
)
from ai.backend.manager.services.groups.actions.delete_group import (
    DeleteGroupAction,
    DeleteGroupActionResult,
)
from ai.backend.manager.services.groups.actions.modify_group import (
    ModifyGroupAction,
    ModifyGroupActionResult,
)
from ai.backend.manager.services.groups.actions.purge_group import (
    PurgeGroupAction,
    PurgeGroupActionResult,
)
from ai.backend.manager.services.groups.service import GroupService


class GroupProcessors:
    create_group: ActionProcessor[CreateGroupAction, CreateGroupActionResult]
    modify_group: ActionProcessor[ModifyGroupAction, ModifyGroupActionResult]
    delete_group: ActionProcessor[DeleteGroupAction, DeleteGroupActionResult]
    purge_group: ActionProcessor[PurgeGroupAction, PurgeGroupActionResult]

    def __init__(self, group_service: GroupService) -> None:
        self.create_group = ActionProcessor(group_service.create_group)
        self.modify_group = ActionProcessor(group_service.modify_group)
        self.delete_group = ActionProcessor(group_service.delete_group)
        self.purge_group = ActionProcessor(group_service.purge_group)
