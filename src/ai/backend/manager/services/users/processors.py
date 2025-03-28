from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.users.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.users.service import UserService


class UserProcessors:
    create_user: ActionProcessor[CreateUserAction, CreateUserActionResult]

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service
