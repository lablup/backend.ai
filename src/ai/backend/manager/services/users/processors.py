from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.users.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.users.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
)
from ai.backend.manager.services.users.service import UserService


class UserProcessors:
    create_user: ActionProcessor[CreateUserAction, CreateUserActionResult]
    modify_user: ActionProcessor[ModifyUserAction, ModifyUserActionResult]

    def __init__(self, user_service: UserService) -> None:
        self.create_user = ActionProcessor(user_service.create_user)
        self.modify_user = ActionProcessor(user_service.modify_user)
