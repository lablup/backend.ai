from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.users.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.users.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.users.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
)
from ai.backend.manager.services.users.actions.purge_user import (
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.users.service import UserService


class UserProcessors:
    create_user: ActionProcessor[CreateUserAction, CreateUserActionResult]
    modify_user: ActionProcessor[ModifyUserAction, ModifyUserActionResult]
    delete_user: ActionProcessor[DeleteUserAction, DeleteUserActionResult]
    purge_user: ActionProcessor[PurgeUserAction, PurgeUserActionResult]

    def __init__(self, user_service: UserService) -> None:
        self.create_user = ActionProcessor(user_service.create_user)
        self.modify_user = ActionProcessor(user_service.modify_user)
        self.delete_user = ActionProcessor(user_service.delete_user)
        self.purge_user = ActionProcessor(user_service.purge_user)
