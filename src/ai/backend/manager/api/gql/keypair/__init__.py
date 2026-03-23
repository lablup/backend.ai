"""Keypair GraphQL API package."""

from .resolver import (
    issue_my_keypair,
    my_keypairs,
    revoke_my_keypair,
    switch_my_main_access_key,
    update_my_keypair,
)

__all__ = [
    "issue_my_keypair",
    "my_keypairs",
    "revoke_my_keypair",
    "switch_my_main_access_key",
    "update_my_keypair",
]
