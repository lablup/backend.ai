"""
Request DTOs for auth DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import AliasChoices, Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.auth.types import AuthTokenType

__all__ = (
    "AuthorizeInput",
    "GetRoleInput",
    "SignupInput",
    "SignoutInput",
    "UpdateFullNameInput",
    "UpdatePasswordInput",
    "UpdatePasswordNoAuthInput",
    "UploadSSHKeypairInput",
    "VerifyAuthInput",
)


class AuthorizeInput(BaseRequestModel):
    """Input for authorizing a user and obtaining API credentials."""

    type: AuthTokenType = Field(
        description="Token type to issue: 'keypair' for HMAC auth or 'jwt' for stateless auth",
    )
    domain: str = Field(
        min_length=1,
        max_length=64,
        description="Domain (tenant) the user belongs to; users are scoped per domain",
    )
    username: str = Field(
        min_length=1,
        max_length=256,
        description="Login identifier (email address or username)",
    )
    password: str = Field(
        min_length=1,
        description="Login password, verified against the stored hash",
    )
    stoken: str | None = Field(
        default=None,
        description="Secondary token forwarded to auth hook plugins (e.g., for 2FA)",
        validation_alias=AliasChoices("stoken", "sToken"),
    )


class SignupInput(BaseRequestModel):
    """Input for signing up a new user. Created with INACTIVE status; requires separate activation."""

    domain: str = Field(
        min_length=1,
        max_length=64,
        description="Domain (tenant) to create the user in",
    )
    email: str = Field(
        min_length=1,
        max_length=256,
        description="Email for the account; must be globally unique, also used as username if not specified",
    )
    password: str = Field(
        min_length=1,
        description="Initial password; validated via VERIFY_PASSWORD_FORMAT hook",
    )
    username: str | None = Field(
        default=None,
        max_length=256,
        description="Display username; defaults to email if omitted",
    )
    full_name: str | None = Field(
        default=None,
        max_length=256,
        description="User's full name for display; defaults to empty string",
    )
    description: str | None = Field(
        default=None,
        max_length=1024,
        description="Free-text account description; defaults to empty string",
    )

    @field_validator("email")
    @classmethod
    def email_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("email must not be blank or whitespace-only")
        return stripped

    @field_validator("username")
    @classmethod
    def username_strip_whitespace(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return v.strip() or None

    @field_validator("full_name")
    @classmethod
    def full_name_strip_whitespace(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return v.strip() or None


class SignoutInput(BaseRequestModel):
    """Input for deactivating a user account (sets INACTIVE, does not delete)."""

    email: str = Field(
        min_length=1,
        max_length=256,
        description="Email of the account to deactivate; must match the requester's own email",
        validation_alias=AliasChoices("email", "username"),
    )
    password: str = Field(
        min_length=1,
        description="Current password for identity confirmation",
    )

    @field_validator("email")
    @classmethod
    def email_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("email must not be blank or whitespace-only")
        return stripped


class VerifyAuthInput(BaseRequestModel):
    """Input for verifying that the current API credentials are valid."""

    echo: str = Field(
        min_length=1,
        max_length=256,
        description="Arbitrary string echoed back to confirm auth is working",
    )


class GetRoleInput(BaseRequestModel):
    """Input for getting the user's roles at global, domain, and optionally group scope."""

    group: UUID | None = Field(
        default=None,
        description="Group (project) ID to also query group-level role; errors if not a member",
    )


class UpdateFullNameInput(BaseRequestModel):
    """Input for updating the authenticated user's display full name."""

    email: str = Field(
        min_length=1,
        max_length=256,
        description="Email of the user to update",
    )
    full_name: str = Field(
        min_length=1,
        max_length=256,
        description="New full name to set",
    )

    @field_validator("email")
    @classmethod
    def email_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("email must not be blank or whitespace-only")
        return stripped

    @field_validator("full_name")
    @classmethod
    def full_name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("full_name must not be blank or whitespace-only")
        return stripped


class UpdatePasswordInput(BaseRequestModel):
    """Input for updating the authenticated user's password with confirmation."""

    old_password: str = Field(
        min_length=1,
        description="Current password for identity verification",
    )
    new_password: str = Field(
        min_length=1,
        description="Desired new password; validated via VERIFY_PASSWORD_FORMAT hook",
    )
    new_password_confirm: str = Field(
        min_length=1,
        description="New password confirmation; must match new_password exactly",
    )


class UpdatePasswordNoAuthInput(BaseRequestModel):
    """Input for updating an expired password without API auth.
    Only available when max_password_age is configured."""

    domain: str = Field(
        min_length=1,
        max_length=64,
        description="Domain (tenant) the user belongs to",
    )
    username: str = Field(
        min_length=1,
        max_length=256,
        description="Login identifier (email or username)",
    )
    current_password: str = Field(
        min_length=1,
        description="Current (expired) password for verification",
    )
    new_password: str = Field(
        min_length=1,
        description="New password; must differ from current password",
    )


class UploadSSHKeypairInput(BaseRequestModel):
    """Input for uploading an SSH keypair. The pair is validated for consistency."""

    pubkey: str = Field(
        min_length=1,
        description="SSH public key in standard format (e.g., 'ssh-rsa AAAA...')",
    )
    privkey: str = Field(
        min_length=1,
        description="SSH private key in PEM format",
    )

    @field_validator("pubkey")
    @classmethod
    def pubkey_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("pubkey must not be blank or whitespace-only")
        return stripped

    @field_validator("privkey")
    @classmethod
    def privkey_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("privkey must not be blank or whitespace-only")
        return stripped
