"""Auth API request DTOs for headers."""

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class SignupHeader(BaseRequestModel):
    """Header parameter for the signup endpoint."""

    accept_language: str = Field(
        default="en-us",
        validation_alias="Accept-Language",
        description="Language tags of the client; the first one becomes the new user's language",
    )
