"""Keypair GraphQL API package."""

from .resolver import issue_my_keypair, revoke_my_keypair, switch_my_main_access_key

__all__ = [
    "issue_my_keypair",
    "revoke_my_keypair",
    "switch_my_main_access_key",
]
