"""
Request DTOs for auth system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel

from .types import AuthTokenType

__all__ = (
    "AuthorizeRequest",
    "GetRoleRequest",
    "SignupRequest",
    "SignoutRequest",
    "UpdateFullNameRequest",
    "UpdatePasswordRequest",
    "UpdatePasswordNoAuthRequest",
    "UploadSSHKeypairRequest",
)


class AuthorizeRequest(BaseRequestModel):
    """Request to authorize a user."""

    type: AuthTokenType = Field(description="Authentication type (keypair or jwt)")
    domain: str = Field(description="Domain name")
    username: str = Field(description="Username or email")
    password: str = Field(description="Password")
    stoken: Optional[str] = Field(
        default=None,
        description="Session token",
        validation_alias=AliasChoices("stoken", "sToken"),
    )


class GetRoleRequest(BaseRequestModel):
    """Request to get user role."""

    group: Optional[UUID] = Field(default=None, description="Group ID to check role for")


class SignupRequest(BaseRequestModel):
    """Request to sign up a new user."""

    domain: str = Field(description="Domain name")
    email: str = Field(description="Email address")
    password: str = Field(description="Password")
    username: Optional[str] = Field(default=None, description="Username")
    full_name: Optional[str] = Field(default=None, description="Full name")
    description: Optional[str] = Field(default=None, description="Description")


class SignoutRequest(BaseRequestModel):
    """Request to sign out a user."""

    email: Optional[str] = Field(default=None, description="Email address")
    username: Optional[str] = Field(default=None, description="Username (alias for email)")
    password: str = Field(description="Password")

    @model_validator(mode="after")
    def validate_email_or_username(self) -> SignoutRequest:
        """Ensure either email or username is provided, prefer email."""
        if self.email is None and self.username is None:
            raise ValueError("Either email or username must be provided")
        # If only username is provided, use it as email
        if self.email is None and self.username is not None:
            object.__setattr__(self, "email", self.username)
        return self


class UpdateFullNameRequest(BaseRequestModel):
    """Request to update user's full name."""

    email: str = Field(description="Email address")
    full_name: str = Field(description="New full name")


class UpdatePasswordRequest(BaseRequestModel):
    """Request to update password (authenticated)."""

    old_password: str = Field(description="Current password")
    new_password: str = Field(description="New password")
    new_password2: str = Field(description="New password confirmation")


class UpdatePasswordNoAuthRequest(BaseRequestModel):
    """Request to update password without authentication."""

    domain: str = Field(description="Domain name")
    username: str = Field(description="Username or email")
    current_password: str = Field(description="Current password")
    new_password: str = Field(description="New password")


class UploadSSHKeypairRequest(BaseRequestModel):
    """Request to upload SSH keypair."""

    pubkey: str = Field(description="SSH public key")
    privkey: str = Field(description="SSH private key")
