"""
Request DTOs for auth system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import AliasChoices, Field

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
    "VerifyAuthRequest",
)


class AuthorizeRequest(BaseRequestModel):
    """Request to authorize a user and obtain API credentials."""

    type: AuthTokenType = Field(
        description="Token type to issue: 'keypair' for HMAC auth or 'jwt' for stateless auth",
    )
    domain: str = Field(
        description="Domain (tenant) the user belongs to; users are scoped per domain",
    )
    username: str = Field(
        description="Login identifier (email address or username)",
    )
    password: str = Field(
        description="Login password, verified against the stored hash",
    )
    stoken: Optional[str] = Field(
        default=None,
        description="Secondary token forwarded to auth hook plugins (e.g., for 2FA)",
        validation_alias=AliasChoices("stoken", "sToken"),
    )


class GetRoleRequest(BaseRequestModel):
    """Request to get the user's roles at global, domain, and optionally group scope."""

    group: Optional[UUID] = Field(
        default=None,
        description="Group (project) ID to also query group-level role; errors if not a member",
    )


class SignupRequest(BaseRequestModel):
    """Request to sign up a new user. Created with INACTIVE status; requires separate activation."""

    domain: str = Field(description="Domain (tenant) to create the user in")
    email: str = Field(
        description="Email for the account; must be globally unique, also used as username if not specified",
    )
    password: str = Field(
        description="Initial password; validated via VERIFY_PASSWORD_FORMAT hook",
    )
    username: Optional[str] = Field(
        default=None,
        description="Display username; defaults to email if omitted",
    )
    full_name: Optional[str] = Field(
        default=None,
        description="User's full name for display; defaults to empty string",
    )
    description: Optional[str] = Field(
        default=None,
        description="Free-text account description; defaults to empty string",
    )


class SignoutRequest(BaseRequestModel):
    """Request to deactivate a user account (sets INACTIVE, does not delete)."""

    email: str = Field(
        description="Email of the account to deactivate; must match the requester's own email",
        validation_alias=AliasChoices("email", "username"),
    )
    password: str = Field(description="Current password for identity confirmation")


class UpdateFullNameRequest(BaseRequestModel):
    """Request to update the authenticated user's display full name."""

    email: str = Field(description="Email of the user to update")
    full_name: str = Field(description="New full name to set")


class UpdatePasswordRequest(BaseRequestModel):
    """Request to update the authenticated user's password with confirmation."""

    old_password: str = Field(description="Current password for identity verification")
    new_password: str = Field(
        description="Desired new password; validated via VERIFY_PASSWORD_FORMAT hook"
    )
    new_password2: str = Field(
        description="New password confirmation; must match new_password exactly"
    )


class UpdatePasswordNoAuthRequest(BaseRequestModel):
    """Request to update an expired password without API auth.
    Only available when max_password_age is configured."""

    domain: str = Field(description="Domain (tenant) the user belongs to")
    username: str = Field(description="Login identifier (email or username)")
    current_password: str = Field(description="Current (expired) password for verification")
    new_password: str = Field(description="New password; must differ from current password")


class UploadSSHKeypairRequest(BaseRequestModel):
    """Request to upload an SSH keypair. The pair is validated for consistency."""

    pubkey: str = Field(description="SSH public key in standard format (e.g., 'ssh-rsa AAAA...')")
    privkey: str = Field(description="SSH private key in PEM format")


class VerifyAuthRequest(BaseRequestModel):
    """Request to verify that the current API credentials are valid."""

    echo: str = Field(description="Arbitrary string echoed back to confirm auth is working")
